"""
Farmer input inventory (Domains 21-24, docs/audit/c04_inputs.md): the
farmer's OWN on-farm stock of seeds/fertilizer/crop-protection/bio-input,
entirely separate from the marketplace's `DealerProduct.stock_quantity`
(the dealer's sellable stock). Creation is manual (farmer records what
they hold) - this phase does not auto-create an inventory row when an
order is delivered; that would be a reasonable future enhancement using
the exact same `create_item`/`restock` functions, not a redesign.

Low-stock and expiry alerts both use a "fires once per episode" gate
(`low_stock_alerted_at`/`expiry_alerted_at`) rather than relying solely on
the Notification table's dedup_key, so a farmer who keeps recording usage
against an already-low item isn't renotified on every call, but IS
renotified if they restock above threshold and then run low again.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.input_inventory import InputInventoryItem
from app.models.notification import NotificationCategory, NotificationPriority
from app.repositories import input_inventory_repository, product_repository, user_repository
from app.schemas.input_inventory import (
    InputInventoryItemCreateRequest,
    InputInventoryItemResponse,
    InputInventoryListResponse,
    QuantityCorrectionRequest,
    RestockRequest,
    UsageRecordRequest,
)
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.weather_alert_rules import AlertCandidate


def create_item(db: Session, farmer_id: str, payload: InputInventoryItemCreateRequest) -> InputInventoryItemResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    product = None
    if payload.product_id is not None:
        product = product_repository.get_product(db, payload.product_id)
        if product is None:
            raise AppError(error_codes.NOT_FOUND, "Product not found.", 404)

    item = InputInventoryItem(
        farmer_id=farmer_uuid,
        product_id=payload.product_id,
        category=payload.category.value,
        custom_name=payload.custom_name,
        quantity=payload.quantity,
        unit=payload.unit,
        low_stock_threshold=payload.low_stock_threshold,
        expiry_date=payload.expiry_date,
    )
    input_inventory_repository.create(db, item)
    AuditLogger(db).log("INPUT_INVENTORY_CREATED", actor_id=farmer_id, actor_role="farmer", entity="input_inventory_item", entity_id=str(item.id))
    db.commit()
    db.refresh(item)
    return _to_response(item, product)


def list_items(db: Session, farmer_id: str) -> InputInventoryListResponse:
    items = input_inventory_repository.list_for_farmer(db, uuid.UUID(farmer_id))
    return InputInventoryListResponse(items=[_to_response(i, _resolve_product(db, i)) for i in items])


def get_item(db: Session, farmer_id: str, item_id: uuid.UUID) -> InputInventoryItemResponse:
    item = _get_owned_or_404(db, farmer_id, item_id)
    return _to_response(item, _resolve_product(db, item))


def record_usage(db: Session, farmer_id: str, item_id: uuid.UUID, payload: UsageRecordRequest) -> InputInventoryItemResponse:
    item = _get_owned_or_404(db, farmer_id, item_id)
    if payload.quantity_used > item.quantity:
        raise AppError(error_codes.VALIDATION_ERROR, "Cannot record usage greater than the remaining quantity.", 422)

    item.quantity -= payload.quantity_used
    AuditLogger(db).log(
        "INPUT_INVENTORY_USAGE_RECORDED", actor_id=farmer_id, actor_role="farmer",
        entity="input_inventory_item", entity_id=str(item.id),
    )
    db.commit()
    _check_low_stock(db, farmer_id, item)
    db.refresh(item)
    return _to_response(item, _resolve_product(db, item))


def restock(db: Session, farmer_id: str, item_id: uuid.UUID, payload: RestockRequest) -> InputInventoryItemResponse:
    item = _get_owned_or_404(db, farmer_id, item_id)
    item.quantity += payload.quantity_added
    AuditLogger(db).log("INPUT_INVENTORY_RESTOCKED", actor_id=farmer_id, actor_role="farmer", entity="input_inventory_item", entity_id=str(item.id))
    db.commit()
    _check_low_stock(db, farmer_id, item)  # clears the alert gate if now back above threshold
    db.refresh(item)
    return _to_response(item, _resolve_product(db, item))


def correct_quantity(db: Session, farmer_id: str, item_id: uuid.UUID, payload: QuantityCorrectionRequest) -> InputInventoryItemResponse:
    item = _get_owned_or_404(db, farmer_id, item_id)
    item.quantity = payload.new_quantity
    # AuditLog.action is String(200) with no separate free-text detail
    # column - the reason is appended (truncated to stay well within
    # that limit) rather than adding a new column to a shared table.
    AuditLogger(db).log(
        f"INPUT_INVENTORY_CORRECTED: {payload.reason[:150]}", actor_id=farmer_id, actor_role="farmer",
        entity="input_inventory_item", entity_id=str(item.id),
    )
    db.commit()
    _check_low_stock(db, farmer_id, item)
    db.refresh(item)
    return _to_response(item, _resolve_product(db, item))


def _get_owned_or_404(db: Session, farmer_id: str, item_id: uuid.UUID) -> InputInventoryItem:
    item = input_inventory_repository.get_owned(db, item_id, uuid.UUID(farmer_id))
    if item is None:
        raise AppError(error_codes.NOT_FOUND, "Input inventory item not found.", 404)
    return item


def _resolve_product(db: Session, item: InputInventoryItem):
    return product_repository.get_product(db, item.product_id) if item.product_id else None


def _display_name(item: InputInventoryItem, product) -> str:
    if product is not None:
        return product.name
    return item.custom_name or "input"


def _to_response(item: InputInventoryItem, product) -> InputInventoryItemResponse:
    is_low_stock = item.low_stock_threshold is not None and item.quantity <= item.low_stock_threshold
    return InputInventoryItemResponse(
        id=item.id,
        product_id=item.product_id,
        product_name=product.name if product is not None else None,
        category=item.category,
        custom_name=item.custom_name,
        quantity=item.quantity,
        unit=item.unit,
        low_stock_threshold=item.low_stock_threshold,
        is_low_stock=is_low_stock,
        expiry_date=item.expiry_date,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _check_low_stock(db: Session, farmer_id: str, item: InputInventoryItem) -> None:
    """D22-06/D24-08: fires a STOCK_ALERT notification the first time
    quantity drops to/below the threshold, then stays quiet until the
    farmer restocks above it again (clearing the gate) - never spams on
    every subsequent usage call while still low."""
    if item.low_stock_threshold is None:
        return

    if item.quantity <= item.low_stock_threshold:
        if item.low_stock_alerted_at is not None:
            return
        product = _resolve_product(db, item)
        candidate = AlertCandidate(
            category=NotificationCategory.STOCK_ALERT,
            priority=NotificationPriority.MEDIUM,
            message_key="INPUT_LOW_STOCK",
            message_params={"item_name": _display_name(item, product), "quantity": str(item.quantity), "unit": item.unit},
            dedup_suffix=f"low_stock:{item.id}:{item.updated_at.isoformat()}",
        )
        language_code = _language_for(db, farmer_id)
        notification_service.create_alert_notification(
            db, farmer_id, candidate, dedup_scope=f"input_inventory:{item.id}", language_code=language_code,
            related_entity_type="input_inventory_item", related_entity_id=str(item.id),
        )
        item.low_stock_alerted_at = datetime.now(timezone.utc)
        db.commit()
    elif item.low_stock_alerted_at is not None:
        item.low_stock_alerted_at = None
        db.commit()


def _language_for(db: Session, farmer_id: str) -> str:
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    if user and getattr(user, "farmer_profile", None):
        return user.farmer_profile.preferred_language_code
    return "en"


def run_expiry_check_sweep(db: Session, settings: Settings) -> int:
    """D24-09: proactive expiry warning, run by the background scheduler
    (app/services/scheduler.py) - not farmer-visible-screen-triggered, so
    it fires even if the farmer never opens the inventory screen."""
    cutoff = date.today() + timedelta(days=settings.input_expiry_warning_days)
    items = input_inventory_repository.list_expiring_unalerted(db, on_or_before=cutoff)

    alerted = 0
    for item in items:
        product = _resolve_product(db, item)
        candidate = AlertCandidate(
            category=NotificationCategory.STOCK_ALERT,
            priority=NotificationPriority.MEDIUM,
            message_key="INPUT_EXPIRY_WARNING",
            message_params={"item_name": _display_name(item, product), "expiry_date": item.expiry_date.isoformat()},
            dedup_suffix=f"expiry_warning:{item.id}",
        )
        language_code = _language_for(db, str(item.farmer_id))
        created = notification_service.create_alert_notification(
            db, str(item.farmer_id), candidate, dedup_scope=f"input_inventory:{item.id}", language_code=language_code,
            related_entity_type="input_inventory_item", related_entity_id=str(item.id),
        )
        item.expiry_alerted_at = datetime.now(timezone.utc)
        db.commit()
        if created is not None:
            alerted += 1

    return alerted

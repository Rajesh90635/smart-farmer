"""
Order service. Cart = a DRAFT order per (farmer, dealer) pair - no
separate Cart/CartItem tables (see app/models/order.py's docstring).

ABSOLUTE RULE: prices are NEVER trusted from the client. Every checkout
recalculates subtotal/discount/tax/delivery/final amounts SERVER-SIDE
from the current DealerProduct.price at confirmation time, and freezes
the result onto Order/OrderItem - the client-supplied cart quantities are
the only client input that matters; every price figure is server-computed.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.dealer_product import DealerProduct
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import ProductStatus
from app.models.professional_profile import VerificationStatus
from app.repositories import dealer_product_repository, order_repository, product_repository, professional_repository
from app.schemas.order import CartItemAddRequest, CartItemUpdateRequest, CheckoutRequest, OrderListResponse, OrderResponse
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition


def _get_or_create_draft(db: Session, farmer_id: uuid.UUID, dealer_id: uuid.UUID) -> Order:
    draft = order_repository.get_draft_order(db, farmer_id, dealer_id)
    if draft is not None:
        return draft
    draft = Order(farmer_id=farmer_id, dealer_id=dealer_id, status=OrderStatus.DRAFT)
    order_repository.create_order(db, draft)
    db.flush()
    return draft


def add_to_cart(db: Session, farmer_id: str, payload: CartItemAddRequest) -> OrderResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    listing = dealer_product_repository.get_by_id(db, payload.dealer_product_id)
    if listing is None or not listing.is_available:
        raise AppError(error_codes.NOT_FOUND, "Product listing not found or unavailable.", 404)

    draft = _get_or_create_draft(db, farmer_uuid, listing.dealer_id)

    existing_item = order_repository.get_item_by_dealer_product(db, draft.id, listing.id)
    if existing_item is not None:
        existing_item.quantity += payload.quantity
    else:
        order_repository.create_item(
            db,
            OrderItem(order_id=draft.id, dealer_product_id=listing.id, product_name_snapshot=_product_display_name(db, listing), quantity=payload.quantity),
        )

    db.commit()
    db.refresh(draft)
    return OrderResponse.model_validate(draft)


def update_cart_item(db: Session, farmer_id: str, order_id: uuid.UUID, dealer_product_id: uuid.UUID, payload: CartItemUpdateRequest) -> OrderResponse:
    draft = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if draft is None or draft.status != OrderStatus.DRAFT:
        raise AppError(error_codes.NOT_FOUND, "Cart not found.", 404)

    item = order_repository.get_item_by_dealer_product(db, draft.id, dealer_product_id)
    if item is None:
        raise AppError(error_codes.NOT_FOUND, "Item not found in cart.", 404)

    item.quantity = payload.quantity
    db.commit()
    db.refresh(draft)
    return OrderResponse.model_validate(draft)


def remove_cart_item(db: Session, farmer_id: str, order_id: uuid.UUID, dealer_product_id: uuid.UUID) -> OrderResponse:
    draft = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if draft is None or draft.status != OrderStatus.DRAFT:
        raise AppError(error_codes.NOT_FOUND, "Cart not found.", 404)

    item = order_repository.get_item_by_dealer_product(db, draft.id, dealer_product_id)
    if item is None:
        raise AppError(error_codes.NOT_FOUND, "Item not found in cart.", 404)

    order_repository.delete_item(db, item)
    db.commit()
    db.refresh(draft)
    return OrderResponse.model_validate(draft)


def get_cart(db: Session, farmer_id: str, order_id: uuid.UUID) -> OrderResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    return OrderResponse.model_validate(order)


def checkout(db: Session, farmer_id: str, order_id: uuid.UUID, payload: CheckoutRequest, settings: Settings) -> OrderResponse:
    farmer_uuid = uuid.UUID(farmer_id)

    existing = order_repository.get_by_idempotency_key(db, payload.idempotency_key)
    if existing is not None:
        return OrderResponse.model_validate(existing)

    order = order_repository.get_order_owned_by_farmer(db, order_id, farmer_uuid)
    if order is None or order.status != OrderStatus.DRAFT:
        raise AppError(error_codes.VALIDATION_ERROR, "This order cannot be checked out (not found or not in draft).", 422)

    if not order.items:
        raise AppError(error_codes.VALIDATION_ERROR, "Cannot check out an empty cart.", 422)

    dealer = professional_repository.get_by_id(db, order.dealer_id)
    if dealer is None or dealer.verification_status != VerificationStatus.VERIFIED:
        raise AppError(error_codes.VALIDATION_ERROR, "This dealer is no longer verified. Please remove these items.", 422)

    subtotal = Decimal("0")
    for item in order.items:
        listing = dealer_product_repository.get_by_id(db, item.dealer_product_id)
        if listing is None or not listing.is_available:
            raise AppError(error_codes.VALIDATION_ERROR, f"'{item.product_name_snapshot}' is no longer available.", 422)
        if listing.stock_quantity < item.quantity:
            raise AppError(error_codes.VALIDATION_ERROR, f"Insufficient stock for '{item.product_name_snapshot}'.", 422)

        # Re-verify product safety status at the moment of checkout - a
        # product approved when listed may have been suspended/recalled
        # since, or the listing's own batch may have expired. Found
        # missing while writing docs/PRODUCT_SAFETY.md and cross-checking
        # its claims against the actual code - this was a real gap, not a
        # documented-then-implemented feature.
        product = product_repository.get_product(db, listing.product_id)
        if product is None or product.status != ProductStatus.APPROVED:
            raise AppError(error_codes.VALIDATION_ERROR, f"'{item.product_name_snapshot}' is no longer available for purchase.", 422)
        if listing.is_expired(datetime.now(timezone.utc).date()):
            raise AppError(error_codes.VALIDATION_ERROR, f"'{item.product_name_snapshot}' has expired and cannot be ordered.", 422)

        item.unit_price = listing.price
        item.discount_amount = Decimal("0")
        item.tax_amount = (listing.price * item.quantity * Decimal(str(settings.order_default_tax_percent)) / Decimal("100")).quantize(Decimal("0.01"))
        item.final_item_amount = (listing.price * item.quantity) + item.tax_amount - item.discount_amount
        subtotal += listing.price * item.quantity

    discount = Decimal("0")
    delivery_fee = Decimal(str(settings.order_default_delivery_fee))
    tax = sum((item.tax_amount or Decimal("0")) for item in order.items)
    final_amount = subtotal - discount + delivery_fee + tax

    order.subtotal_amount = subtotal
    order.discount_amount = discount
    order.delivery_fee_amount = delivery_fee
    order.tax_amount = tax
    order.final_amount = final_amount
    order.delivery_area = payload.delivery_area
    order.idempotency_key = payload.idempotency_key
    # Pass through PENDING_CONFIRMATION explicitly rather than jumping
    # straight DRAFT -> CONFIRMED - keeps this call consistent with the
    # transition map instead of silently bypassing it. Found while wiring
    # this up: the map didn't allow a direct DRAFT->CONFIRMED jump, and
    # skipping the intermediate state here would have made the map a lie.
    apply_transition(order, OrderStatus.PENDING_CONFIRMATION)
    apply_transition(order, OrderStatus.CONFIRMED)
    order.confirmed_at = datetime.now(timezone.utc)

    for item in order.items:
        listing = dealer_product_repository.get_by_id(db, item.dealer_product_id)
        listing.stock_quantity -= item.quantity

    AuditLogger(db).log("ORDER_CONFIRMED", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(order)
    return OrderResponse.model_validate(order)


def get_my_order(db: Session, farmer_id: str, order_id: uuid.UUID) -> OrderResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    return OrderResponse.model_validate(order)


def list_my_orders(db: Session, farmer_id: str, *, limit: int = 50, offset: int = 0) -> OrderListResponse:
    items, total = order_repository.list_orders_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return OrderListResponse(items=[OrderResponse.model_validate(o) for o in items], total=total)


def cancel_order(db: Session, farmer_id: str, order_id: uuid.UUID) -> OrderResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    apply_transition(order, OrderStatus.CANCELLED)
    order.cancelled_at = datetime.now(timezone.utc)

    AuditLogger(db).log("ORDER_CANCELLED", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(order)
    return OrderResponse.model_validate(order)


def _product_display_name(db: Session, listing: DealerProduct) -> str:
    from app.repositories import product_repository

    product = product_repository.get_product(db, listing.product_id)
    return product.name if product else "Unknown product"

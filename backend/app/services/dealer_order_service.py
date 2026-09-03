"""
Dealer-side order actions: accept/reject a PAID order, then progress
through fulfillment. Every action re-verifies the caller is the actual
dealer on the order via professional_repository + ownership, never
trusting a role claim alone.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.order import OrderStatus
from app.repositories import dealer_product_repository, order_repository, professional_repository
from app.schemas.order import DealerOrderActionRequest, OrderListResponse, OrderResponse
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition


def _get_order_for_dealer_or_404(db: Session, user_id: str, order_id: uuid.UUID):
    dealer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if dealer is None:
        raise AppError(error_codes.NOT_FOUND, "No dealer profile found for this account.", 404)
    order = order_repository.get_order_owned_by_dealer(db, order_id, dealer.id)
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    return order, dealer


def list_dealer_orders(db: Session, user_id: str, *, limit: int = 50, offset: int = 0) -> OrderListResponse:
    dealer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if dealer is None:
        raise AppError(error_codes.NOT_FOUND, "No dealer profile found for this account.", 404)
    items, total = order_repository.list_orders_for_dealer(db, dealer.id, limit=limit, offset=offset)
    return OrderListResponse(items=[OrderResponse.model_validate(o) for o in items], total=total)


def accept_order(db: Session, user_id: str, order_id: uuid.UUID) -> OrderResponse:
    order, dealer = _get_order_for_dealer_or_404(db, user_id, order_id)
    apply_transition(order, OrderStatus.ACCEPTED_BY_DEALER)
    AuditLogger(db).log("ORDER_ACCEPTED_BY_DEALER", actor_id=user_id, actor_role="dealer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(order)
    return OrderResponse.model_validate(order)


def reject_order(db: Session, user_id: str, order_id: uuid.UUID, payload: DealerOrderActionRequest) -> OrderResponse:
    order, dealer = _get_order_for_dealer_or_404(db, user_id, order_id)
    apply_transition(order, OrderStatus.REJECTED)
    order.rejection_reason = payload.reason

    # Lock every listing (in a fixed order, mirroring order_service.checkout)
    # before restocking - a concurrent rejection of a DIFFERENT order that
    # shares one of these products could otherwise read the same
    # stock_quantity and lose one of the two increments.
    for item in sorted(order.items, key=lambda i: str(i.dealer_product_id)):
        listing = dealer_product_repository.get_by_id_for_update(db, item.dealer_product_id)
        if listing:
            listing.stock_quantity += item.quantity

    AuditLogger(db).log("ORDER_REJECTED", actor_id=user_id, actor_role="dealer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(order)
    return OrderResponse.model_validate(order)


def advance_fulfillment(db: Session, user_id: str, order_id: uuid.UUID, target_status: OrderStatus) -> OrderResponse:
    order, dealer = _get_order_for_dealer_or_404(db, user_id, order_id)
    apply_transition(order, target_status)
    AuditLogger(db).log(f"ORDER_{target_status.value.upper()}", actor_id=user_id, actor_role="dealer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(order)
    return OrderResponse.model_validate(order)

"""
Delivery: deliberately simple status tracking, not a logistics platform.
A Delivery row is created once an order reaches ACCEPTED_BY_DEALER, and
its status is updated by the dealer alongside the Order's own fulfillment
status (kept as two objects, not merged, since Delivery may later be
handed to a distinct transporter role - not built this phase).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.delivery import Delivery, DeliveryStatus
from app.repositories import order_repository, professional_repository
from app.schemas.order import DeliveryResponse, DeliveryUpdateRequest
from app.services.audit_logger import AuditLogger


def get_or_create_delivery(db: Session, order_id: uuid.UUID) -> Delivery:
    delivery = order_repository.get_delivery_for_order(db, order_id)
    if delivery is not None:
        return delivery
    delivery = Delivery(order_id=order_id)
    order_repository.create_delivery(db, delivery)
    return delivery


def update_delivery(db: Session, user_id: str, order_id: uuid.UUID, payload: DeliveryUpdateRequest) -> DeliveryResponse:
    dealer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if dealer is None:
        raise AppError(error_codes.NOT_FOUND, "No dealer profile found for this account.", 404)

    order = order_repository.get_order_owned_by_dealer(db, order_id, dealer.id)
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    delivery = get_or_create_delivery(db, order.id)
    delivery.status = payload.status
    if payload.tracking_note is not None:
        delivery.tracking_note = payload.tracking_note
    if payload.estimated_delivery_date is not None:
        delivery.estimated_delivery_date = payload.estimated_delivery_date

    now = datetime.now(timezone.utc)
    if payload.status == DeliveryStatus.PICKED_UP and delivery.dispatched_at is None:
        delivery.dispatched_at = now
    if payload.status == DeliveryStatus.DELIVERED:
        delivery.delivered_at = now

    AuditLogger(db).log("DELIVERY_STATUS_UPDATED", actor_id=user_id, actor_role="dealer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(delivery)
    return DeliveryResponse.model_validate(delivery)


def get_delivery_for_farmer(db: Session, farmer_id: str, order_id: uuid.UUID) -> DeliveryResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    delivery = order_repository.get_delivery_for_order(db, order.id)
    if delivery is None:
        raise AppError(error_codes.NOT_FOUND, "No delivery record yet for this order.", 404)
    return DeliveryResponse.model_validate(delivery)

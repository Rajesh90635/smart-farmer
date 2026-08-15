"""
Dispute/refund foundation. A dispute can only be filed on a DELIVERED or
OUT_FOR_DELIVERY order (matches the transition map's DISPUTED sources).
Refund is never auto-completed - `resolve_dispute` requires an explicit
admin decision (status + refund_type), and "COMPLETED" here means the
sandbox/manual bookkeeping was marked complete, never a real money
transfer (see docs/PAYMENT_SANDBOX.md - no real refund API exists yet).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.order import OrderStatus
from app.models.order_dispute import DisputeStatus, OrderDispute, Refund, RefundStatus, RefundType
from app.repositories import order_repository
from app.schemas.order import DisputeCreateRequest, DisputeResolveRequest, DisputeResponse, RefundResponse
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition


def create_dispute(db: Session, farmer_id: str, order_id: uuid.UUID, payload: DisputeCreateRequest) -> DisputeResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    order = order_repository.get_order_owned_by_farmer(db, order_id, farmer_uuid)
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    if order.status not in (OrderStatus.DELIVERED, OrderStatus.OUT_FOR_DELIVERY):
        raise AppError(error_codes.VALIDATION_ERROR, "A dispute can only be filed for a delivered or out-for-delivery order.", 422)

    if order_repository.get_dispute_for_order(db, order.id) is not None:
        raise AppError(error_codes.VALIDATION_ERROR, "A dispute already exists for this order.", 409)

    apply_transition(order, OrderStatus.DISPUTED)

    dispute = OrderDispute(order_id=order.id, farmer_id=farmer_uuid, reason=payload.reason, description=payload.description, evidence_note=payload.evidence_note)
    order_repository.create_dispute(db, dispute)

    AuditLogger(db).log("ORDER_DISPUTE_CREATED", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(dispute)
    return DisputeResponse.model_validate(dispute)


def resolve_dispute(db: Session, admin_user_id: str, dispute_id: uuid.UUID, payload: DisputeResolveRequest) -> DisputeResponse:
    dispute = order_repository.get_dispute(db, dispute_id)
    if dispute is None:
        raise AppError(error_codes.NOT_FOUND, "Dispute not found.", 404)

    dispute.status = payload.status
    if payload.status in (DisputeStatus.RESOLVED, DisputeStatus.REJECTED):
        dispute.resolved_at = datetime.now(timezone.utc)

    order = order_repository.get_order_by_id_admin(db, dispute.order_id)

    if payload.status == DisputeStatus.RESOLVED and payload.refund_type and payload.refund_type != RefundType.NO_REFUND:
        refund = Refund(order_id=dispute.order_id, dispute_id=dispute.id, refund_type=payload.refund_type, amount=payload.refund_amount, reason=payload.resolution_note)
        order_repository.create_refund(db, refund)
        if order is not None:
            apply_transition(order, OrderStatus.REFUND_PENDING)

    AuditLogger(db).log("ORDER_DISPUTE_RESOLVED", actor_id=admin_user_id, actor_role="admin", entity="order", entity_id=str(dispute.order_id))
    db.commit()
    db.refresh(dispute)
    return DisputeResponse.model_validate(dispute)


def complete_refund(db: Session, admin_user_id: str, order_id: uuid.UUID) -> RefundResponse:
    """SANDBOX/MANUAL bookkeeping only - marks the refund complete without
    any real money movement, since no real payment gateway is integrated
    this phase."""
    refund = order_repository.get_refund_for_order(db, order_id)
    if refund is None:
        raise AppError(error_codes.NOT_FOUND, "No refund found for this order.", 404)

    refund.status = RefundStatus.COMPLETED
    refund.completed_at = datetime.now(timezone.utc)

    order = order_repository.get_order_by_id_admin(db, order_id)
    if order is not None:
        apply_transition(order, OrderStatus.REFUNDED)

    AuditLogger(db).log("REFUND_COMPLETED", actor_id=admin_user_id, actor_role="admin", entity="order", entity_id=str(order_id))
    db.commit()
    db.refresh(refund)
    return RefundResponse.model_validate(refund)


def get_my_dispute(db: Session, farmer_id: str, order_id: uuid.UUID) -> DisputeResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    dispute = order_repository.get_dispute_for_order(db, order.id)
    if dispute is None:
        raise AppError(error_codes.NOT_FOUND, "No dispute found for this order.", 404)
    return DisputeResponse.model_validate(dispute)

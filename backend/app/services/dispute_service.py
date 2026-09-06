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
from app.models.notification import NotificationCategory, NotificationPriority
from app.models.order import OrderStatus
from app.models.order_dispute import DisputeStatus, OrderDispute, Refund, RefundStatus, RefundType
from app.repositories import order_repository, user_repository
from app.schemas.order import DisputeCreateRequest, DisputeListResponse, DisputeResolveRequest, DisputeResponse, RefundResponse
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition
from app.services.weather_alert_rules import AlertCandidate

_OPEN_DISPUTE_STATUSES = [DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ESCALATED]


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
        # D68-02 (docs/audit/FINAL_CANONICAL_group_C.md): refund_amount had
        # no upper-bound check against what the farmer actually paid - an
        # admin typo or bad-faith entry could refund more than the order
        # was ever worth, a real financial-miscalculation/fraud exposure.
        if payload.refund_amount is not None and payload.refund_amount <= 0:
            raise AppError(error_codes.VALIDATION_ERROR, "refund_amount must be greater than zero.", 422)
        if (
            payload.refund_amount is not None
            and order is not None
            and order.final_amount is not None
            and payload.refund_amount > order.final_amount
        ):
            raise AppError(
                error_codes.VALIDATION_ERROR, "refund_amount cannot exceed the order's final_amount.", 422
            )

        refund = Refund(order_id=dispute.order_id, dispute_id=dispute.id, refund_type=payload.refund_type, amount=payload.refund_amount, reason=payload.resolution_note)
        order_repository.create_refund(db, refund)
        if order is not None:
            apply_transition(order, OrderStatus.REFUND_PENDING)

    AuditLogger(db).log("ORDER_DISPUTE_RESOLVED", actor_id=admin_user_id, actor_role="admin", entity="order", entity_id=str(dispute.order_id))
    db.commit()
    db.refresh(dispute)
    if payload.status in (DisputeStatus.RESOLVED, DisputeStatus.REJECTED):
        _notify_dispute_resolved(db, dispute, payload)
    return DisputeResponse.model_validate(dispute)


def _notify_dispute_resolved(db: Session, dispute: OrderDispute, payload: DisputeResolveRequest) -> None:
    """D78-08 (docs/audit/FINAL_CANONICAL_group_D.md): the farmer who filed
    the dispute had no way to learn its outcome except polling the order/
    dispute detail screen themselves."""
    farmer_id = str(dispute.farmer_id)
    user = user_repository.get_by_id(db, dispute.farmer_id)
    language_code = user.farmer_profile.preferred_language_code if user and getattr(user, "farmer_profile", None) else "en"

    if payload.status == DisputeStatus.REJECTED:
        message_key, message_params = "DISPUTE_REJECTED", {}
    elif payload.refund_type and payload.refund_type != RefundType.NO_REFUND:
        message_key, message_params = "DISPUTE_RESOLVED_REFUNDED", {"amount": str(payload.refund_amount)}
    else:
        message_key, message_params = "DISPUTE_RESOLVED_NO_REFUND", {}

    candidate = AlertCandidate(
        category=NotificationCategory.DISPUTE_ALERT,
        priority=NotificationPriority.HIGH,
        message_key=message_key,
        message_params=message_params,
        dedup_suffix=f"dispute_resolved:{dispute.id}",
    )
    notification_service.create_alert_notification(
        db, farmer_id, candidate, dedup_scope=f"farmer:{farmer_id}", language_code=language_code,
        related_entity_type="order_dispute", related_entity_id=str(dispute.id),
    )


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


def list_open_disputes(db: Session, *, limit: int = 50, offset: int = 0) -> DisputeListResponse:
    """The admin discovery endpoint that was missing entirely - resolve_dispute
    already existed, but an admin had no way to find a dispute_id to
    resolve except being told one directly."""
    items, total = order_repository.list_disputes_by_statuses(db, _OPEN_DISPUTE_STATUSES, limit=limit, offset=offset)
    return DisputeListResponse(items=[DisputeResponse.model_validate(d) for d in items], total=total)


def get_my_dispute(db: Session, farmer_id: str, order_id: uuid.UUID) -> DisputeResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    dispute = order_repository.get_dispute_for_order(db, order.id)
    if dispute is None:
        raise AppError(error_codes.NOT_FOUND, "No dispute found for this order.", 404)
    return DisputeResponse.model_validate(dispute)

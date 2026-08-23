"""
Payment service: SANDBOX ONLY this phase. No real gateway is integrated.
`initiate_payment` creates a PENDING Payment and moves the order to
PAYMENT_PENDING; `complete_payment` is a TEST-ONLY endpoint (clearly
documented, not something a real farmer would call in production)
simulating a gateway callback, since there is no real gateway to call
back from.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.repositories import order_repository
from app.schemas.order import PaymentCompleteRequest, PaymentInitiateResponse
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition


def initiate_payment(db: Session, farmer_id: str, order_id: uuid.UUID) -> PaymentInitiateResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    apply_transition(order, OrderStatus.PAYMENT_PENDING)

    payment = Payment(
        order_id=order.id,
        provider=PaymentProvider.SANDBOX,
        status=PaymentStatus.PENDING,
        amount=order.final_amount,
        external_reference=f"sandbox-{uuid.uuid4().hex[:12]}",
    )
    order_repository.create_payment(db, payment)

    AuditLogger(db).log("PAYMENT_INITIATED", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(payment)
    return PaymentInitiateResponse.model_validate(payment)


def complete_payment(db: Session, farmer_id: str, order_id: uuid.UUID, payload: PaymentCompleteRequest) -> PaymentInitiateResponse:
    """SANDBOX/TEST-ONLY: simulates what a real gateway's webhook would
    report. See docs/PAYMENT_SANDBOX.md for why this exists and how it
    must be replaced (not extended) when a real gateway is integrated."""
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    payment = order_repository.get_latest_payment_for_order(db, order.id)
    if payment is None or payment.status != PaymentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "No pending payment found for this order.", 409)

    if payload.succeed:
        payment.status = PaymentStatus.SUCCESS
        payment.completed_at = datetime.now(timezone.utc)
        apply_transition(order, OrderStatus.PAID)
        AuditLogger(db).log("PAYMENT_SUCCESS", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    else:
        payment.status = PaymentStatus.FAILED
        payment.completed_at = datetime.now(timezone.utc)
        AuditLogger(db).log("PAYMENT_FAILED", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))

    db.commit()
    db.refresh(payment)
    return PaymentInitiateResponse.model_validate(payment)

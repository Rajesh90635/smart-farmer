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
from app.models.notification import NotificationCategory, NotificationPriority
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.repositories import order_repository, user_repository
from app.schemas.order import PaymentCompleteRequest, PaymentInitiateResponse
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition
from app.services.weather_alert_rules import AlertCandidate


def initiate_payment(db: Session, farmer_id: str, order_id: uuid.UUID) -> PaymentInitiateResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    existing_payment = order_repository.get_latest_payment_for_order(db, order.id)
    if existing_payment is not None and existing_payment.status == PaymentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "A payment is already in progress for this order.", 409)

    # Real bug fixed here: apply_transition requires an actual state
    # change, but a farmer retrying after a failed payment finds the order
    # ALREADY sitting in PAYMENT_PENDING - complete_payment's failure path
    # never moves it anywhere else, and PAYMENT_PENDING has no allowed
    # self-transition in ALLOWED_ORDER_TRANSITIONS. This 409'd every retry
    # attempt with no way forward. Only transition when genuinely entering
    # PAYMENT_PENDING for the first time.
    if order.status != OrderStatus.PAYMENT_PENDING:
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
    if not payload.succeed:
        # D64-06/D66-04 (docs/audit/c10_payments_finance.md): previously
        # only an audit log entry, never farmer-visible - a real gap once
        # a real gateway's asynchronous webhook replaces this sandbox
        # callback (the farmer wouldn't be watching the response then).
        _notify_payment_failed(db, farmer_id, payment)
    db.refresh(payment)
    return PaymentInitiateResponse.model_validate(payment)


def _notify_payment_failed(db: Session, farmer_id: str, payment: Payment) -> None:
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    language_code = user.farmer_profile.preferred_language_code if user and getattr(user, "farmer_profile", None) else "en"
    candidate = AlertCandidate(
        category=NotificationCategory.PAYMENT_ALERT,
        priority=NotificationPriority.HIGH,
        message_key="PAYMENT_FAILED",
        message_params={"amount": str(payment.amount)},
        dedup_suffix=f"payment_failed:{payment.id}",
    )
    notification_service.create_alert_notification(
        db, farmer_id, candidate, dedup_scope=f"farmer:{farmer_id}", language_code=language_code,
        related_entity_type="payment", related_entity_id=str(payment.id),
    )

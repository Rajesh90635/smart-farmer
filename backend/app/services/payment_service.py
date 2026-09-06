"""
Payment service. `initiate_payment` creates a PENDING Payment and moves
the order to PAYMENT_PENDING; `complete_payment` is a TEST-ONLY endpoint
(clearly documented, not something a real farmer would call in
production) simulating a gateway callback, since only the sandbox
adapter is actually implemented (see
app/services/payment/payment_gateway_provider.py, D90-10).
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.notification import NotificationCategory, NotificationPriority
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.repositories import order_repository, sale_order_repository, user_repository
from app.schemas.order import PaymentCompleteRequest, PaymentInitiateResponse, PaymentListResponse, PaymentResponse
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.order_transitions import apply_transition
from app.services.payment.payment_gateway_provider import PaymentGatewayProvider
from app.services.weather_alert_rules import AlertCandidate

_PROVIDER_NAME_TO_ENUM = {"sandbox": PaymentProvider.SANDBOX}


def initiate_payment(
    db: Session, farmer_id: str, order_id: uuid.UUID, payment_provider: PaymentGatewayProvider, amount: Decimal | None = None
) -> PaymentInitiateResponse:
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    existing_payment = order_repository.get_latest_payment_for_order(db, order.id)
    if existing_payment is not None and existing_payment.status == PaymentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "A payment is already in progress for this order.", 409)

    # D65-01/D65-02: `amount` is the actually-tendered amount, not always
    # the full order value - a farmer may pay in installments (D65-03).
    # Omitted amount defaults to the full remaining balance, so a single
    # full payment (the only case before this scenario) still behaves
    # identically to before.
    paid_so_far = order_repository.sum_successful_payment_amount_for_order(db, order.id)
    remaining = order.final_amount - paid_so_far
    if remaining <= 0:
        raise AppError(error_codes.VALIDATION_ERROR, "This order is already fully paid.", 409)

    tendered = amount if amount is not None else remaining
    if tendered > remaining:
        raise AppError(error_codes.VALIDATION_ERROR, f"Amount exceeds the remaining balance of {remaining}.", 422)

    result = payment_provider.initiate_payment(amount=tendered, reference_hint=str(order.id))
    if not result.available:
        raise AppError(error_codes.PAYMENT_PROVIDER_UNAVAILABLE, "Payment is temporarily unavailable. Please try again shortly.", 503)

    # Real bug fixed here: apply_transition requires an actual state
    # change, but a farmer retrying after a failed payment finds the order
    # ALREADY sitting in PAYMENT_PENDING - complete_payment's failure path
    # never moves it anywhere else, and PAYMENT_PENDING has no allowed
    # self-transition in ALLOWED_ORDER_TRANSITIONS. This 409'd every retry
    # attempt with no way forward. Only transition when genuinely entering
    # PAYMENT_PENDING for the first time.
    if order.status != OrderStatus.PAYMENT_PENDING:
        apply_transition(order, OrderStatus.PAYMENT_PENDING)

    installment_number = order_repository.count_payments_for_order(db, order.id) + 1
    payment = Payment(
        order_id=order.id,
        provider=_PROVIDER_NAME_TO_ENUM[result.provider_name],
        status=PaymentStatus.PENDING,
        amount=tendered,
        installment_number=installment_number,
        external_reference=result.external_reference,
    )
    order_repository.create_payment(db, payment)

    AuditLogger(db).log("PAYMENT_INITIATED", actor_id=farmer_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    db.commit()
    db.refresh(payment)
    return PaymentInitiateResponse.model_validate(payment)


def complete_payment(
    db: Session, farmer_id: str, order_id: uuid.UUID, payload: PaymentCompleteRequest, payment_provider: PaymentGatewayProvider
) -> PaymentInitiateResponse:
    """SANDBOX/TEST-ONLY: simulates what a real gateway's webhook would
    report. See docs/PAYMENT_ARCHITECTURE.md for why this exists and how
    it must be replaced (not extended) when a real gateway is integrated -
    refuses to run at all unless the configured provider is
    sandbox-completable (a real gateway's completion must arrive via an
    actual webhook, never a farmer-callable endpoint)."""
    if not payment_provider.is_sandbox_completable:
        raise AppError(
            error_codes.PAYMENT_PROVIDER_UNAVAILABLE,
            "This payment method does not support manual completion - it is confirmed by the gateway's own callback.",
            409,
        )

    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    payment = order_repository.get_latest_payment_for_order(db, order.id)
    if payment is None or payment.status != PaymentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "No pending payment found for this order.", 409)

    if payload.succeed:
        payment.status = PaymentStatus.SUCCESS
        payment.completed_at = datetime.now(timezone.utc)
        db.flush()  # so the balance sum below sees this payment as SUCCESS (autoflush is off for this session)
        # D65-03: a partial payment leaves genuine balance remaining - the
        # order stays PAYMENT_PENDING so the farmer can pay the rest via
        # another initiate_payment call, rather than being force-marked
        # PAID on the first (possibly partial) successful attempt.
        paid_so_far = order_repository.sum_successful_payment_amount_for_order(db, order.id)
        if paid_so_far >= order.final_amount:
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


def list_payments_for_order(db: Session, farmer_id: str, order_id: uuid.UUID) -> PaymentListResponse:
    """D65-05: every attempt against this order's balance, successful or
    not - existing failed/retry Payment rows already accumulate in the DB
    today, just previously unreachable via any API."""
    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(farmer_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)

    payments = order_repository.list_payments_for_order(db, order.id)
    return PaymentListResponse(items=[PaymentResponse.model_validate(p) for p in payments], total=len(payments))


def run_payment_timeout_sweep(db: Session, settings: Settings) -> int:
    """D66-03 (docs/audit/FINAL_CANONICAL_group_C.md): PaymentStatus.TIMEOUT
    existed but nothing ever assigned it - a payment could sit PENDING
    forever with no resolution. Payment is shared across dealer orders
    (order_id) and marketplace sales (sale_order_id), so this one sweep
    covers both sources rather than needing two."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.payment_timeout_minutes)
    stale_payments = order_repository.list_stale_pending_payments(db, cutoff)

    timed_out = 0
    for payment in stale_payments:
        payment.status = PaymentStatus.TIMEOUT
        payment.completed_at = datetime.now(timezone.utc)

        farmer_id = _resolve_farmer_id_for_payment(db, payment)
        AuditLogger(db).log(
            "PAYMENT_TIMED_OUT", actor_id=None, actor_role="scheduler", entity="payment", entity_id=str(payment.id)
        )
        db.commit()

        if farmer_id is not None:
            _notify_payment_timed_out(db, farmer_id, payment)
            timed_out += 1

    return timed_out


def _resolve_farmer_id_for_payment(db: Session, payment: Payment) -> str | None:
    if payment.order_id is not None:
        order = order_repository.get_order_by_id_admin(db, payment.order_id)
        return str(order.farmer_id) if order is not None else None
    if payment.sale_order_id is not None:
        sale = sale_order_repository.get_sale_by_id(db, payment.sale_order_id)
        return str(sale.farmer_id) if sale is not None else None
    return None


def _notify_payment_timed_out(db: Session, farmer_id: str, payment: Payment) -> None:
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    language_code = user.farmer_profile.preferred_language_code if user and getattr(user, "farmer_profile", None) else "en"
    candidate = AlertCandidate(
        category=NotificationCategory.PAYMENT_ALERT,
        priority=NotificationPriority.HIGH,
        message_key="PAYMENT_TIMED_OUT",
        message_params={"amount": str(payment.amount)},
        dedup_suffix=f"payment_timed_out:{payment.id}",
    )
    notification_service.create_alert_notification(
        db, farmer_id, candidate, dedup_scope=f"farmer:{farmer_id}", language_code=language_code,
        related_entity_type="payment", related_entity_id=str(payment.id),
    )


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

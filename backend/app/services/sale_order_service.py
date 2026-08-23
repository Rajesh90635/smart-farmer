"""
Sale order lifecycle. Payment and Delivery REUSE the exact tables built
in Prompt 9 (via the sale_order_id column added this phase) - no
SalePayment/SaleDelivery duplicate tables. Every function here that
touches Payment/Delivery sets sale_order_id and leaves order_id NULL,
mirroring exactly how Prompt 9's code sets order_id and leaves
sale_order_id NULL - "exactly one is set" is maintained by construction.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.sale_dispute import QualityDispute, SaleDispute, SaleFeedback
from app.models.sale_order import ALLOWED_SALE_ORDER_TRANSITIONS, CANCELLATION_REASONS, SaleOrder, SaleOrderStatus
from app.repositories import harvest_repository, order_repository, professional_repository, sale_order_repository
from app.schemas.marketplace import (
    QualityDisputeCreateRequest,
    SaleCancelRequest,
    SaleDisputeCreateRequest,
    SaleDisputeResponse,
    SaleFeedbackCreateRequest,
    SaleOrderListResponse,
    SaleOrderResponse,
)
from app.services.audit_logger import AuditLogger


def _apply_transition(sale: SaleOrder, target: SaleOrderStatus) -> None:
    allowed = ALLOWED_SALE_ORDER_TRANSITIONS.get(sale.status, set())
    if target not in allowed:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot change sale status from '{sale.status.value}' to '{target.value}'.", 409)
    sale.status = target


def get_my_sale(db: Session, farmer_id: str, sale_id: uuid.UUID) -> SaleOrderResponse:
    sale = sale_order_repository.get_sale_owned_by_farmer(db, sale_id, uuid.UUID(farmer_id))
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)
    return SaleOrderResponse.model_validate(sale)


def list_my_sales(db: Session, farmer_id: str, *, limit: int = 50, offset: int = 0) -> SaleOrderListResponse:
    items, total = sale_order_repository.list_sales_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return SaleOrderListResponse(items=[SaleOrderResponse.model_validate(s) for s in items], total=total)


def _get_sale_for_buyer_or_404(db: Session, user_id: str, sale_id: uuid.UUID) -> SaleOrder:
    buyer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if buyer is None:
        raise AppError(error_codes.NOT_FOUND, "No buyer profile found for this account.", 404)
    sale = sale_order_repository.get_sale_owned_by_buyer(db, sale_id, buyer.id)
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)
    return sale


def list_my_purchases(db: Session, user_id: str, *, limit: int = 50, offset: int = 0) -> SaleOrderListResponse:
    buyer = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if buyer is None:
        raise AppError(error_codes.NOT_FOUND, "No buyer profile found for this account.", 404)
    items, total = sale_order_repository.list_sales_for_buyer(db, buyer.id, limit=limit, offset=offset)
    return SaleOrderListResponse(items=[SaleOrderResponse.model_validate(s) for s in items], total=total)


def farmer_accept(db: Session, farmer_id: str, sale_id: uuid.UUID) -> SaleOrderResponse:
    sale = sale_order_repository.get_sale_owned_by_farmer(db, sale_id, uuid.UUID(farmer_id))
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)
    _apply_transition(sale, SaleOrderStatus.ACCEPTED)
    AuditLogger(db).log("SALE_ACCEPTED", actor_id=farmer_id, actor_role="farmer", entity="sale_order", entity_id=str(sale.id))
    db.commit()
    db.refresh(sale)
    return SaleOrderResponse.model_validate(sale)


def advance_status(db: Session, farmer_id: str, sale_id: uuid.UUID, target_status: SaleOrderStatus) -> SaleOrderResponse:
    sale = sale_order_repository.get_sale_owned_by_farmer(db, sale_id, uuid.UUID(farmer_id))
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)
    _apply_transition(sale, target_status)
    AuditLogger(db).log(f"SALE_{target_status.value.upper()}", actor_id=farmer_id, actor_role="farmer", entity="sale_order", entity_id=str(sale.id))
    db.commit()
    db.refresh(sale)
    return SaleOrderResponse.model_validate(sale)


def buyer_confirm_delivery(db: Session, user_id: str, sale_id: uuid.UUID) -> SaleOrderResponse:
    sale = _get_sale_for_buyer_or_404(db, user_id, sale_id)
    _apply_transition(sale, SaleOrderStatus.PAYMENT_PENDING)
    AuditLogger(db).log("SALE_DELIVERY_CONFIRMED_BY_BUYER", actor_id=user_id, actor_role="buyer", entity="sale_order", entity_id=str(sale.id))
    db.commit()
    db.refresh(sale)
    return SaleOrderResponse.model_validate(sale)


def initiate_payment(db: Session, user_id: str, sale_id: uuid.UUID) -> Payment:
    sale = _get_sale_for_buyer_or_404(db, user_id, sale_id)

    payment = Payment(
        sale_order_id=sale.id, order_id=None, provider=PaymentProvider.SANDBOX, status=PaymentStatus.PENDING,
        amount=sale.net_value, external_reference=f"sandbox-sale-{uuid.uuid4().hex[:12]}",
    )
    order_repository.create_payment(db, payment)
    AuditLogger(db).log("SALE_PAYMENT_INITIATED", actor_id=user_id, actor_role="buyer", entity="sale_order", entity_id=str(sale.id))
    db.commit()
    db.refresh(payment)
    return payment


def complete_payment(db: Session, user_id: str, sale_id: uuid.UUID, succeed: bool) -> Payment:
    sale = _get_sale_for_buyer_or_404(db, user_id, sale_id)

    payment = db.execute(
        select(Payment).where(Payment.sale_order_id == sale.id).order_by(Payment.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    if payment is None or payment.status != PaymentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "No pending payment found for this sale.", 409)

    if succeed:
        payment.status = PaymentStatus.SUCCESS
        payment.completed_at = datetime.now(timezone.utc)
        _apply_transition(sale, SaleOrderStatus.PAID)
        AuditLogger(db).log("SALE_PAYMENT_SUCCESS", actor_id=user_id, actor_role="buyer", entity="sale_order", entity_id=str(sale.id))
    else:
        payment.status = PaymentStatus.FAILED
        payment.completed_at = datetime.now(timezone.utc)
        AuditLogger(db).log("SALE_PAYMENT_FAILED", actor_id=user_id, actor_role="buyer", entity="sale_order", entity_id=str(sale.id))

    db.commit()
    db.refresh(payment)
    return payment


def cancel_sale(db: Session, user_id: str, sale_id: uuid.UUID, payload: SaleCancelRequest, role: str) -> SaleOrderResponse:
    if payload.reason not in CANCELLATION_REASONS:
        raise AppError(error_codes.VALIDATION_ERROR, f"'{payload.reason}' is not a valid cancellation reason.", 422)

    if role == "farmer":
        sale = sale_order_repository.get_sale_owned_by_farmer(db, sale_id, uuid.UUID(user_id))
    else:
        sale = _get_sale_for_buyer_or_404(db, user_id, sale_id)
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)

    _apply_transition(sale, SaleOrderStatus.CANCELLED)
    sale.cancellation_reason = payload.reason

    listing = harvest_repository.get_listing_for_update(db, sale.harvest_listing_id)
    if listing is not None:
        listing.quantity_available += sale.quantity
        listing.is_active = True

    AuditLogger(db).log("SALE_CANCELLED", actor_id=user_id, actor_role=role, entity="sale_order", entity_id=str(sale.id))
    db.commit()
    db.refresh(sale)
    return SaleOrderResponse.model_validate(sale)


def create_dispute(db: Session, user_id: str, sale_id: uuid.UUID, payload: SaleDisputeCreateRequest, role: str) -> SaleDisputeResponse:
    if role == "farmer":
        sale = sale_order_repository.get_sale_owned_by_farmer(db, sale_id, uuid.UUID(user_id))
    else:
        sale = _get_sale_for_buyer_or_404(db, user_id, sale_id)
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)

    if sale.status not in (SaleOrderStatus.DELIVERED, SaleOrderStatus.PAYMENT_PENDING, SaleOrderStatus.PAID):
        raise AppError(error_codes.VALIDATION_ERROR, "A dispute can only be filed once the sale has reached delivery or later.", 422)

    _apply_transition(sale, SaleOrderStatus.DISPUTED)

    dispute = SaleDispute(sale_order_id=sale.id, raised_by_user_id=uuid.UUID(user_id), raised_by_role=role, reason=payload.reason, description=payload.description)
    sale_order_repository.create_dispute(db, dispute)

    AuditLogger(db).log("SALE_DISPUTE_CREATED", actor_id=user_id, actor_role=role, entity="sale_order", entity_id=str(sale.id))
    db.commit()
    db.refresh(dispute)
    return SaleDisputeResponse.model_validate(dispute)


def add_quality_dispute_details(db: Session, dispute_id: uuid.UUID, payload: QualityDisputeCreateRequest) -> None:
    dispute = sale_order_repository.get_dispute(db, dispute_id)
    if dispute is None:
        raise AppError(error_codes.NOT_FOUND, "Dispute not found.", 404)

    sale = sale_order_repository.get_sale_by_id(db, dispute.sale_order_id)
    quality_dispute = QualityDispute(
        sale_dispute_id=dispute.id,
        agreed_grade=sale.quality_grade_snapshot if sale else None,
        buyer_claimed_grade=payload.buyer_claimed_grade,
        evidence_note=payload.evidence_note,
    )
    sale_order_repository.create_quality_dispute(db, quality_dispute)
    db.commit()


def submit_feedback(db: Session, user_id: str, sale_id: uuid.UUID, payload: SaleFeedbackCreateRequest, role: str) -> None:
    if role == "farmer":
        sale = sale_order_repository.get_sale_owned_by_farmer(db, sale_id, uuid.UUID(user_id))
    else:
        sale = _get_sale_for_buyer_or_404(db, user_id, sale_id)
    if sale is None:
        raise AppError(error_codes.NOT_FOUND, "Sale not found.", 404)

    if sale_order_repository.get_feedback(db, sale_id, role) is not None:
        raise AppError(error_codes.VALIDATION_ERROR, "Feedback has already been submitted for this sale.", 409)

    feedback = SaleFeedback(
        sale_order_id=sale.id, given_by_user_id=uuid.UUID(user_id), given_by_role=role,
        helpful=payload.helpful, rating=payload.rating, feedback_details=payload.feedback_details, feedback_text=payload.feedback_text,
    )
    sale_order_repository.create_feedback(db, feedback)
    db.commit()

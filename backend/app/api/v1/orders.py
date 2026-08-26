"""
Cart (= DRAFT order) + checkout + order tracking + dealer fulfillment +
payment + delivery + dispute/refund endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.models.order import OrderStatus
from app.schemas.order import (
    CartItemAddRequest,
    CartItemUpdateRequest,
    CheckoutRequest,
    DealerOrderActionRequest,
    DeliveryResponse,
    DeliveryUpdateRequest,
    DisputeCreateRequest,
    DisputeListResponse,
    DisputeResolveRequest,
    DisputeResponse,
    OrderListResponse,
    OrderResponse,
    PaymentCompleteRequest,
    PaymentInitiateResponse,
    RefundResponse,
)
from app.services import dealer_order_service, delivery_service, dispute_service, order_service, payment_service

router = APIRouter(tags=["orders"])


@router.post("/cart", response_model=OrderResponse, status_code=201)
def add_to_cart(
    payload: CartItemAddRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.add_to_cart(db, current_user.user_id, payload)


@router.get("/cart/{order_id}", response_model=OrderResponse)
def get_cart(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.get_cart(db, current_user.user_id, order_id)


@router.put("/cart/{order_id}/items/{dealer_product_id}", response_model=OrderResponse)
def update_cart_item(
    order_id: uuid.UUID,
    dealer_product_id: uuid.UUID,
    payload: CartItemUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.update_cart_item(db, current_user.user_id, order_id, dealer_product_id, payload)


@router.delete("/cart/{order_id}/items/{dealer_product_id}", response_model=OrderResponse)
def remove_cart_item(
    order_id: uuid.UUID,
    dealer_product_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.remove_cart_item(db, current_user.user_id, order_id, dealer_product_id)


@router.post("/orders/{order_id}/checkout", response_model=OrderResponse)
def checkout(
    order_id: uuid.UUID,
    payload: CheckoutRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OrderResponse:
    return order_service.checkout(db, current_user.user_id, order_id, payload, settings)


@router.get("/orders", response_model=OrderListResponse)
def list_my_orders(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    return order_service.list_my_orders(db, current_user.user_id, limit=limit, offset=offset)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.get_my_order(db, current_user.user_id, order_id)


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.cancel_order(db, current_user.user_id, order_id)


@router.post("/orders/{order_id}/pay", response_model=PaymentInitiateResponse)
def initiate_payment(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PaymentInitiateResponse:
    return payment_service.initiate_payment(db, current_user.user_id, order_id)


@router.post("/orders/{order_id}/pay/complete", response_model=PaymentInitiateResponse)
def complete_payment_sandbox(
    order_id: uuid.UUID,
    payload: PaymentCompleteRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PaymentInitiateResponse:
    """SANDBOX/TEST-ONLY - see docs/PAYMENT_SANDBOX.md. Simulates a
    gateway callback since no real gateway is integrated this phase."""
    return payment_service.complete_payment(db, current_user.user_id, order_id, payload)


@router.get("/orders/{order_id}/delivery", response_model=DeliveryResponse)
def get_delivery(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> DeliveryResponse:
    return delivery_service.get_delivery_for_farmer(db, current_user.user_id, order_id)


@router.post("/orders/{order_id}/confirm-delivery", response_model=OrderResponse)
def confirm_delivery(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Farmer explicitly confirms RECEIVED - a dealer marking DELIVERED
    (via dealer_order_service) records dispatch-side completion; this is
    the farmer's own confirmation of receipt, kept as a separate action
    per Requirement 43 rather than assumed automatically."""
    from app.core import error_codes
    from app.core.errors import AppError
    from app.repositories import order_repository
    from app.services.audit_logger import AuditLogger

    order = order_repository.get_order_owned_by_farmer(db, order_id, uuid.UUID(current_user.user_id))
    if order is None:
        raise AppError(error_codes.NOT_FOUND, "Order not found.", 404)
    if order.status != OrderStatus.DELIVERED:
        raise AppError(error_codes.VALIDATION_ERROR, "This order has not been marked delivered by the dealer yet.", 422)

    AuditLogger(db).log("ORDER_DELIVERY_CONFIRMED_BY_FARMER", actor_id=current_user.user_id, actor_role="farmer", entity="order", entity_id=str(order.id))
    db.commit()
    from app.schemas.order import OrderResponse as _OrderResponse

    return _OrderResponse.model_validate(order)


@router.post("/orders/{order_id}/dispute", response_model=DisputeResponse, status_code=201)
def create_dispute(
    order_id: uuid.UUID,
    payload: DisputeCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> DisputeResponse:
    return dispute_service.create_dispute(db, current_user.user_id, order_id, payload)


@router.get("/orders/{order_id}/dispute", response_model=DisputeResponse)
def get_dispute(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> DisputeResponse:
    return dispute_service.get_my_dispute(db, current_user.user_id, order_id)


@router.get("/disputes", response_model=DisputeListResponse)
def list_open_disputes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> DisputeListResponse:
    return dispute_service.list_open_disputes(db, limit=limit, offset=offset)


@router.post("/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
def resolve_dispute(
    dispute_id: uuid.UUID,
    payload: DisputeResolveRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> DisputeResponse:
    return dispute_service.resolve_dispute(db, current_user.user_id, dispute_id, payload)


@router.post("/orders/{order_id}/refund/complete", response_model=RefundResponse)
def complete_refund(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> RefundResponse:
    return dispute_service.complete_refund(db, current_user.user_id, order_id)


# --- Dealer-side ---

@router.get("/dealer/orders", response_model=OrderListResponse)
def list_dealer_orders(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    return dealer_order_service.list_dealer_orders(db, current_user.user_id, limit=limit, offset=offset)


@router.post("/dealer/orders/{order_id}/accept", response_model=OrderResponse)
def accept_order(
    order_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return dealer_order_service.accept_order(db, current_user.user_id, order_id)


@router.post("/dealer/orders/{order_id}/reject", response_model=OrderResponse)
def reject_order(
    order_id: uuid.UUID,
    payload: DealerOrderActionRequest,
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return dealer_order_service.reject_order(db, current_user.user_id, order_id, payload)


@router.post("/dealer/orders/{order_id}/advance", response_model=OrderResponse)
def advance_order(
    order_id: uuid.UUID,
    target_status: OrderStatus,
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> OrderResponse:
    """A single endpoint for the linear PREPARING -> READY_FOR_DISPATCH ->
    DISPATCHED -> OUT_FOR_DELIVERY -> DELIVERED chain, since each step has
    identical authorization/logic - only the target status differs."""
    return dealer_order_service.advance_fulfillment(db, current_user.user_id, order_id, target_status)


@router.put("/dealer/orders/{order_id}/delivery", response_model=DeliveryResponse)
def update_delivery(
    order_id: uuid.UUID,
    payload: DeliveryUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.DEALER.value, Role.TRADER.value)),
    db: Session = Depends(get_db),
) -> DeliveryResponse:
    return delivery_service.update_delivery(db, current_user.user_id, order_id, payload)

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.delivery import DeliveryStatus
from app.models.order import OrderStatus
from app.models.order_dispute import DisputeReason, DisputeStatus, RefundStatus, RefundType
from app.models.payment import PaymentProvider, PaymentStatus


class CartItemAddRequest(BaseModel):
    dealer_product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    dealer_product_id: uuid.UUID
    product_name_snapshot: str
    quantity: int
    unit_price: Decimal | None
    final_item_amount: Decimal | None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    dealer_id: uuid.UUID
    status: OrderStatus
    subtotal_amount: Decimal | None
    discount_amount: Decimal | None
    delivery_fee_amount: Decimal | None
    tax_amount: Decimal | None
    final_amount: Decimal | None
    rejection_reason: str | None
    items: list[OrderItemResponse]
    created_at: datetime
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int


class CheckoutRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=100)
    delivery_area: dict | None = None


class DealerOrderActionRequest(BaseModel):
    reason: str | None = None


class PaymentInitiateResponse(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    provider: PaymentProvider
    status: PaymentStatus
    amount: Decimal

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Payment's PK column is named `id`, not `payment_id` - map it
        # explicitly rather than renaming the model's PK to match this
        # one response schema's preferred field name.
        if hasattr(obj, "id") and not hasattr(obj, "payment_id"):
            return super().model_validate(
                {"payment_id": obj.id, "order_id": obj.order_id, "provider": obj.provider, "status": obj.status, "amount": obj.amount}, **kwargs
            )
        return super().model_validate(obj, **kwargs)


class PaymentCompleteRequest(BaseModel):
    """Sandbox-only: lets a test simulate a payment outcome. A real
    gateway would call back via webhook instead - not built this phase."""
    succeed: bool = True


class DeliveryUpdateRequest(BaseModel):
    status: DeliveryStatus
    tracking_note: str | None = None
    estimated_delivery_date: date | None = None


class DeliveryResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    status: DeliveryStatus
    estimated_delivery_date: date | None
    tracking_note: str | None

    model_config = {"from_attributes": True}


class DisputeCreateRequest(BaseModel):
    reason: DisputeReason
    description: str | None = Field(default=None, max_length=1000)
    evidence_note: str | None = Field(default=None, max_length=1000)


class DisputeResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    reason: DisputeReason
    status: DisputeStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DisputeResolveRequest(BaseModel):
    status: DisputeStatus
    refund_type: RefundType | None = None
    refund_amount: Decimal | None = None
    resolution_note: str | None = None


class RefundResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    refund_type: RefundType
    amount: Decimal | None
    status: RefundStatus

    model_config = {"from_attributes": True}

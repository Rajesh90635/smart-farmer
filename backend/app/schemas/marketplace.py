import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.buyer_business_profile import BuyerType
from app.models.buyer_offer import NegotiationParty, OfferStatus
from app.models.sale_dispute import SaleDisputeReason, SaleDisputeStatus
from app.models.sale_order import SaleOrderStatus


class BuyerProfileRegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=200)
    buyer_type: BuyerType
    crops_purchased: list[uuid.UUID] = Field(default_factory=list)
    quality_requirements: str | None = None
    min_quantity: Decimal | None = Field(default=None, gt=0)
    max_quantity: Decimal | None = Field(default=None, gt=0)
    purchase_frequency: str | None = None
    collection_method: str | None = None
    service_area: dict | None = None


class BuyerProfileResponse(BaseModel):
    id: uuid.UUID  # professional_profile id
    display_name: str
    verification_status: str
    buyer_type: BuyerType
    crops_purchased: list[str] | None
    min_quantity: Decimal | None
    max_quantity: Decimal | None
    collection_method: str | None


class OfferCreateRequest(BaseModel):
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    price_per_unit: Decimal = Field(gt=0)
    quality_requirements: str | None = None
    valid_until: datetime | None = None
    collection_terms: str | None = None


class AcceptOfferRequest(BaseModel):
    """`charges` is always farmer-entered, never computed/estimated by the
    backend - matching this app's ledger/cost-estimate convention of never
    fabricating a financial figure. Omitted or 0 means no transport/
    commission/storage cost was deducted from this sale, not that none
    exists in reality."""

    charges: Decimal = Field(default=Decimal("0"), ge=0)


class OfferResponse(BaseModel):
    id: uuid.UUID
    harvest_listing_id: uuid.UUID
    buyer_id: uuid.UUID
    quantity: Decimal
    unit: str
    price_per_unit: Decimal
    status: OfferStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class OfferListResponse(BaseModel):
    items: list[OfferResponse]
    total: int


class CounterOfferCreateRequest(BaseModel):
    price_per_unit: Decimal = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    message: str | None = Field(default=None, max_length=500)


class CounterOfferResponse(BaseModel):
    id: uuid.UUID
    buyer_offer_id: uuid.UUID
    proposed_by: NegotiationParty
    price_per_unit: Decimal
    quantity: Decimal
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleOrderResponse(BaseModel):
    id: uuid.UUID
    harvest_listing_id: uuid.UUID
    buyer_id: uuid.UUID
    crop_id: uuid.UUID
    quantity: Decimal
    unit: str
    price_per_unit: Decimal
    gross_value: Decimal
    charges: Decimal
    net_value: Decimal
    collection_method: str
    status: SaleOrderStatus
    cancellation_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleOrderListResponse(BaseModel):
    items: list[SaleOrderResponse]
    total: int


class SaleCancelRequest(BaseModel):
    reason: str


class SaleDisputeCreateRequest(BaseModel):
    reason: SaleDisputeReason
    description: str | None = Field(default=None, max_length=1000)


class SaleDisputeResponse(BaseModel):
    id: uuid.UUID
    sale_order_id: uuid.UUID
    reason: SaleDisputeReason
    status: SaleDisputeStatus
    created_at: datetime
    resolved_at: datetime | None = None
    resolution_note: str | None = None

    model_config = {"from_attributes": True}


class SaleDisputeResolveRequest(BaseModel):
    status: SaleDisputeStatus
    resulting_sale_status: SaleOrderStatus | None = None
    resolution_note: str | None = Field(default=None, max_length=1000)


class SaleDisputeListResponse(BaseModel):
    items: list[SaleDisputeResponse]
    total: int


class QualityDisputeCreateRequest(BaseModel):
    buyer_claimed_grade: str
    description: str | None = Field(default=None, max_length=1000)
    evidence_note: str | None = Field(default=None, max_length=1000)


class SaleFeedbackCreateRequest(BaseModel):
    helpful: bool | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback_details: dict | None = None
    feedback_text: str | None = Field(default=None, max_length=1000)

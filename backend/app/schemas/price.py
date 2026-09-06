import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.price_anomaly_flag import PriceAnomalyLevel
from app.models.reference_price import ReferencePriceSourceType


class ReferencePriceCreateRequest(BaseModel):
    product_id: uuid.UUID
    price: Decimal
    source_type: ReferencePriceSourceType
    source_name: str | None = None
    region: dict | None = None
    effective_date: date


class ReferencePriceResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    price: Decimal
    source_type: ReferencePriceSourceType
    source_name: str | None
    effective_date: date
    # D88-03 (docs/audit/FINAL_CANONICAL_group_D.md): the column already
    # existed on the model - it was simply never exposed in the response.
    retrieved_at: datetime
    # D88-10 (docs/audit/FINAL_CANONICAL_group_D.md): mirrors weather's
    # is_stale convention - set by the service/route layer (needs
    # Settings), defaults to False so a bare model_validate() stays
    # correct anywhere this isn't explicitly computed.
    is_stale: bool = False

    model_config = {"from_attributes": True}


class DealerOfferComparisonResponse(BaseModel):
    dealer_product_id: uuid.UUID
    dealer_id: uuid.UUID
    dealer_price: Decimal
    price_per_unit: Decimal
    unit: str
    stock_quantity: int
    is_available: bool


class PriceComparisonResponse(BaseModel):
    product_id: uuid.UUID
    reference_price: Decimal | None
    reference_price_per_unit: Decimal | None
    reference_source: str | None
    offers: list[DealerOfferComparisonResponse]


class ScamShieldStatusResponse(BaseModel):
    dealer_product_id: uuid.UUID
    price_per_unit: Decimal
    reference_price_per_unit: Decimal | None
    percent_above_reference: float | None
    anomaly_level: str | None  # None = normal
    message: str

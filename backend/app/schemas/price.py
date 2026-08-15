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

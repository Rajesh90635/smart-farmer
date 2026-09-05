import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.product import ProductCategory


class InputInventoryItemCreateRequest(BaseModel):
    product_id: uuid.UUID | None = None
    category: ProductCategory
    custom_name: str | None = Field(default=None, max_length=200)
    quantity: Decimal = Field(ge=0)
    unit: str = Field(min_length=1, max_length=20)
    low_stock_threshold: Decimal | None = Field(default=None, ge=0)
    expiry_date: date | None = None

    @model_validator(mode="after")
    def _require_name_when_no_product(self) -> "InputInventoryItemCreateRequest":
        if self.product_id is None and not self.custom_name:
            raise ValueError("custom_name is required when product_id is not provided.")
        return self


class UsageRecordRequest(BaseModel):
    quantity_used: Decimal = Field(gt=0)
    notes: str | None = Field(default=None, max_length=500)


class RestockRequest(BaseModel):
    quantity_added: Decimal = Field(gt=0)


class QuantityCorrectionRequest(BaseModel):
    new_quantity: Decimal = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


class InputInventoryItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID | None
    product_name: str | None
    category: str
    custom_name: str | None
    quantity: Decimal
    unit: str
    low_stock_threshold: Decimal | None
    is_low_stock: bool
    expiry_date: date | None
    created_at: datetime
    updated_at: datetime


class InputInventoryListResponse(BaseModel):
    items: list[InputInventoryItemResponse]

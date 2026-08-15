import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.product import ProductCategory, ProductStatus


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: ProductCategory
    manufacturer: str | None = None
    active_ingredients: list[str] = Field(default_factory=list)
    pack_size_value: Decimal = Field(gt=0)
    pack_size_unit: str = Field(min_length=1, max_length=20)
    description: str | None = None
    usage_information: str | None = None
    regulatory_info: str | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: ProductCategory
    manufacturer: str | None
    active_ingredients: list[str] | None
    pack_size_value: Decimal
    pack_size_unit: str
    description: str | None
    usage_information: str | None
    status: ProductStatus
    is_test_product: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int


class DealerProductCreateRequest(BaseModel):
    product_id: uuid.UUID
    price: Decimal = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    delivery_area: dict | None = None
    batch_number: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None


class DealerProductUpdateRequest(BaseModel):
    price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_available: bool | None = None
    delivery_area: dict | None = None
    price_change_reason: str | None = None


class DealerProductResponse(BaseModel):
    id: uuid.UUID
    dealer_id: uuid.UUID
    product_id: uuid.UUID
    price: Decimal
    stock_quantity: int
    is_available: bool
    expiry_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DealerProductListResponse(BaseModel):
    items: list[DealerProductResponse]
    total: int

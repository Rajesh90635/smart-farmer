"""
Product: the CONTROLLED master catalog. Dealers select an APPROVED product
to list (see DealerProduct) - they never create arbitrary product names
that bypass approval. Pack size/unit are baked into the product identity
itself (e.g. "Product X, 500ml" and "Product X, 1L" are two separate
Product rows) - the simplest correct way to avoid comparing non-equivalent
quantities.

`usage_information` is deliberately generic/non-prescriptive text (e.g.
"For foliar application" - never a dosage). This field must NEVER contain
dosage/application-rate instructions - that would violate the absolute
"no unsafe AI/platform prescription" rule. Enforced by convention/review,
not a technical filter, since it's admin-entered content.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ProductCategory(str, enum.Enum):
    SEED = "seed"
    FERTILIZER = "fertilizer"
    BIO_INPUT = "bio_input"
    PEST_CONTROL_PRODUCT = "pest_control_product"
    CROP_PROTECTION_PRODUCT = "crop_protection_product"
    EQUIPMENT = "equipment"
    OTHER_AGRICULTURAL_INPUT = "other_agricultural_input"


class ProductStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    RECALLED = "recalled"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        SAEnum(ProductCategory, name="product_category", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    active_ingredients: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pack_size_value: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    pack_size_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulatory_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus, name="product_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=ProductStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    is_test_product: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

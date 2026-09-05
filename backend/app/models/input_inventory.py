"""
InputInventoryItem: a farmer's OWN on-farm stock of a seed/fertilizer/
crop-protection/bio-input - entirely separate from `DealerProduct.stock_quantity`
(the dealer's sellable stock, decremented at checkout). Domain 21/22/23/24
(docs/audit/c04_inputs.md): confirmed by exhaustive search that no such
model existed anywhere before this - `DealerProduct.stock_quantity` and
`OrderItem.quantity` record the marketplace side only, never what a
specific farmer currently possesses.

`category` reuses `Product.category`'s exact vocabulary (imported from
app.models.product, not re-declared) but is stored as a plain string here
rather than a shared native Postgres enum, so this table never needs to
touch/alter the `product_category` enum type `products` already owns -
lower migration risk, and consistent with this project's own precedent of
storing some enum-like values as plain strings (e.g.
`CropHealthCase.requested_professional_role`).

`low_stock_alerted_at`/`expiry_alerted_at` are NOT audit timestamps - they
gate notification dedup so a low-stock or expiry alert fires once per
episode (not on every usage-recording call or every scheduler tick), and
are cleared back to None once the underlying condition is no longer true
(restocked above threshold), so a genuinely new episode alerts again.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InputInventoryItem(Base):
    __tablename__ = "input_inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # a Product.category (ProductCategory) value
    custom_name: Mapped[str | None] = mapped_column(String(200), nullable=True)  # required when product_id is None

    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    low_stock_threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    low_stock_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

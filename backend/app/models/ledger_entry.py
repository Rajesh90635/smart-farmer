"""
LedgerEntry: Phase 29 - Digital Crop Financial Ledger.

Two entry sources, both real, neither fabricated:
1. MANUAL - the farmer types in an expense or revenue line item
   directly. This is the primary, always-available mechanism and works
   for any cost/revenue regardless of whether it passed through this
   platform's own marketplace.
2. SALE_LINKED - imported from the farmer's own COMPLETED SaleOrder
   (Prompt 10 harvest marketplace), traced back to this crop cycle via
   the real existing chain: SaleOrder -> HarvestListing -> HarvestRecord
   .crop_cycle_id. The amount is exactly SaleOrder.net_value - never
   recomputed or adjusted. linked_sale_id has a unique constraint so the
   same sale can never be imported twice.

Added Phase 30: INVOICE_LINKED source - created only via
Invoice.confirm(), never automatically from raw OCR output. The
traceability link is one-directional (Invoice.linked_ledger_entry_id ->
this table) rather than adding a reverse linked_invoice_id column here,
which would create a circular foreign-key dependency between these two
tables for no functional benefit this phase - given an invoice, its
ledger entry is directly queryable; the reverse lookup isn't needed by
anything built so far.

DELIBERATELY NOT built this phase: automatic expense import from Order
(Prompt 9 - agricultural input purchases). Order has no crop_cycle_id
anywhere in its schema - a farmer's dealer purchase isn't currently
traceable to a specific crop cycle at all. Adding that linkage would mean
modifying Order's own schema (a separate, well-tested, unrelated system)
purely to serve this new feature - out of scope for "smallest safe
change." Documented as a real, disclosed limitation.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LedgerEntryType(str, enum.Enum):
    EXPENSE = "expense"
    REVENUE = "revenue"


class LedgerEntrySource(str, enum.Enum):
    MANUAL = "manual"
    SALE_LINKED = "sale_linked"
    INVOICE_LINKED = "invoice_linked"


class LedgerCategory(str, enum.Enum):
    SEED = "seed"
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    IRRIGATION = "irrigation"
    LAND_RENT = "land_rent"
    TRANSPORT = "transport"
    HARVEST_SALE = "harvest_sale"
    OTHER = "other"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("linked_sale_id", name="uq_ledger_entries_linked_sale_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)

    entry_type: Mapped[LedgerEntryType] = mapped_column(
        SAEnum(LedgerEntryType, name="ledger_entry_type", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False, index=True
    )
    category: Mapped[LedgerCategory] = mapped_column(
        SAEnum(LedgerCategory, name="ledger_category", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[LedgerEntrySource] = mapped_column(
        SAEnum(LedgerEntrySource, name="ledger_entry_source", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=LedgerEntrySource.MANUAL,
        nullable=False,
    )
    linked_sale_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_orders.id", ondelete="SET NULL"), nullable=True)

    # Added Phase 31 - optional, nullable, additive. Lets a farmer
    # (optionally) tag WHICH crop stage an expense/revenue entry belongs
    # to, enabling real stage-wise estimated-vs-actual comparison. Every
    # existing row remains valid with this NULL - nothing about Phase 29
    # behavior changes.
    crop_stage_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_stage_definitions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

"""
Invoice: Phase 30 - Invoice OCR + Confirmation.

THE ABSOLUTE SAFETY RULE: extracted_* fields are OCR BEST GUESSES, never
ground truth. They are NEVER written to the financial ledger
automatically. Only confirmed_* fields (set exclusively via the
farmer's own explicit confirm action) are authoritative, and only a
confirm action creates a real LedgerEntry (source=INVOICE_LINKED).

is_confirmed=False means the extracted_* fields are shown to the farmer
for review but have NOT yet become a financial record of any kind.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InvoiceOCRStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InvoiceOCRConfidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)

    image_storage_key: Mapped[str] = mapped_column(String(500), nullable=False)

    ocr_status: Mapped[InvoiceOCRStatus] = mapped_column(
        SAEnum(InvoiceOCRStatus, name="invoice_ocr_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=InvoiceOCRStatus.PENDING,
        nullable=False,
        index=True,
    )
    ocr_raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[InvoiceOCRConfidence | None] = mapped_column(
        SAEnum(InvoiceOCRConfidence, name="invoice_ocr_confidence", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=True
    )
    ocr_unavailable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    extracted_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    extracted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    extracted_vendor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    confirmed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmed_vendor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confirmed_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linked_ledger_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ledger_entries.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

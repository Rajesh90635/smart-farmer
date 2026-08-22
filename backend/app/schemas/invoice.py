import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.invoice import InvoiceOCRConfidence, InvoiceOCRStatus
from app.models.ledger_entry import LedgerCategory


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    ocr_status: InvoiceOCRStatus
    ocr_confidence: InvoiceOCRConfidence | None
    ocr_unavailable_reason: str | None
    extracted_amount: Decimal | None
    extracted_date: date | None
    extracted_vendor_name: str | None
    is_confirmed: bool
    confirmed_amount: Decimal | None
    confirmed_date: date | None
    confirmed_vendor_name: str | None
    confirmed_category: LedgerCategory | None
    linked_ledger_entry_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceConfirmRequest(BaseModel):
    """The farmer's own reviewed/corrected values - NEVER defaulted from
    extracted_* fields silently. Every field is required so the farmer
    must actively confirm each one, even if it happens to match the OCR
    guess exactly."""
    amount: Decimal = Field(gt=0)
    entry_date: date
    vendor_name: str | None = Field(default=None, max_length=200)
    category: LedgerCategory


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]

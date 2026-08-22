import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.ledger_entry import LedgerCategory, LedgerEntrySource, LedgerEntryType


class LedgerEntryCreateRequest(BaseModel):
    entry_type: LedgerEntryType
    category: LedgerCategory
    amount: Decimal = Field(gt=0)
    entry_date: date
    description: str | None = Field(default=None, max_length=1000)
    # Added Phase 31 - optional; omitting it leaves the entry
    # unattributed to any specific stage, exactly as every entry
    # created before this phase already is.
    crop_stage_definition_id: uuid.UUID | None = None


class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    entry_type: LedgerEntryType
    category: LedgerCategory
    amount: Decimal
    entry_date: date
    description: str | None
    source: LedgerEntrySource
    linked_sale_id: uuid.UUID | None
    crop_stage_definition_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LedgerSummaryResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    total_expense: Decimal
    total_revenue: Decimal
    net: Decimal
    entries: list[LedgerEntryResponse]


class LedgerImportSalesResponse(BaseModel):
    imported_count: int
    entries: list[LedgerEntryResponse]

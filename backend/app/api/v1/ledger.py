"""
Ledger endpoints - Phase 29 Digital Crop Financial Ledger.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.ledger import LedgerEntryCreateRequest, LedgerEntryResponse, LedgerImportSalesResponse, LedgerSummaryResponse
from app.services import ledger_service

router = APIRouter(tags=["ledger"])


@router.post("/crop-cycles/{crop_cycle_id}/ledger/entries", response_model=LedgerEntryResponse, status_code=201)
def create_ledger_entry(
    crop_cycle_id: uuid.UUID,
    payload: LedgerEntryCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> LedgerEntryResponse:
    return ledger_service.create_manual_entry(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/ledger", response_model=LedgerSummaryResponse)
def get_ledger_summary(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> LedgerSummaryResponse:
    return ledger_service.get_summary(db, current_user.user_id, crop_cycle_id)


@router.post("/crop-cycles/{crop_cycle_id}/ledger/import-sales", response_model=LedgerImportSalesResponse)
def import_completed_sales(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> LedgerImportSalesResponse:
    return ledger_service.import_completed_sales(db, current_user.user_id, crop_cycle_id)


@router.delete("/ledger/entries/{entry_id}", status_code=204)
def delete_ledger_entry(
    entry_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    ledger_service.delete_entry(db, current_user.user_id, entry_id)

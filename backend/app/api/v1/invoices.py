"""
Invoice endpoints - Phase 30 Invoice OCR + Confirmation.
"""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.ocr_provider_dependency import get_ocr_provider
from app.core.roles import Role
from app.core.storage_dependency import get_file_storage
from app.db.session import get_db
from app.schemas.invoice import InvoiceConfirmRequest, InvoiceListResponse, InvoiceResponse
from app.services import invoice_service
from app.services.ocr.ocr_provider import OCRProvider
from app.services.storage.base import FileStorage

router = APIRouter(tags=["invoices"])


@router.post("/crop-cycles/{crop_cycle_id}/invoices", response_model=InvoiceResponse, status_code=201)
async def upload_invoice(
    crop_cycle_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
    ocr_provider: OCRProvider = Depends(get_ocr_provider),
) -> InvoiceResponse:
    file_bytes = await file.read()
    return invoice_service.upload_invoice(
        db, current_user.user_id, crop_cycle_id, file_bytes, file.filename or "invoice.jpg", file.content_type or "image/jpeg", storage, ocr_provider
    )


@router.get("/crop-cycles/{crop_cycle_id}/invoices", response_model=InvoiceListResponse)
def list_invoices(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InvoiceListResponse:
    return invoice_service.list_invoices(db, current_user.user_id, crop_cycle_id)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    return invoice_service.get_invoice(db, current_user.user_id, invoice_id)


@router.post("/invoices/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: uuid.UUID,
    payload: InvoiceConfirmRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    return invoice_service.confirm_invoice(db, current_user.user_id, invoice_id, payload)


@router.delete("/invoices/{invoice_id}", status_code=204)
def delete_invoice(
    invoice_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
) -> None:
    invoice_service.delete_invoice(db, current_user.user_id, invoice_id, storage)

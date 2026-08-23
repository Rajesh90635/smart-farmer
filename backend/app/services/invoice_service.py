"""
Invoice service. THE ABSOLUTE SAFETY RULE: extracted_* fields (OCR best
guesses) are NEVER written to the ledger. Only confirm_invoice() - which
requires the farmer's own explicit, separately-typed values - ever
creates a real LedgerEntry.
"""
import io
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import get_settings
from app.core.errors import AppError
from app.models.invoice import Invoice, InvoiceOCRConfidence, InvoiceOCRStatus
from app.models.ledger_entry import LedgerEntry, LedgerEntrySource, LedgerEntryType
from app.repositories import crop_cycle_repository, invoice_repository, ledger_entry_repository
from app.schemas.invoice import InvoiceConfirmRequest, InvoiceListResponse, InvoiceResponse
from app.services.audit_logger import AuditLogger
from app.services.ocr.ocr_provider import OCRConfidenceLevel, OCRProvider
from app.services.storage.base import FileStorage


def upload_invoice(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, file_bytes: bytes, file_name: str, content_type: str, storage: FileStorage, ocr_provider: OCRProvider
) -> InvoiceResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    storage_key = storage.save("invoices", file_name, io.BytesIO(file_bytes), content_type)

    invoice = Invoice(farmer_id=farmer_uuid, crop_cycle_id=crop_cycle_id, image_storage_key=storage_key, ocr_status=InvoiceOCRStatus.PROCESSING)
    invoice_repository.create(db, invoice)
    db.flush()

    # OCR runs synchronously - same convention already established for
    # the disease-AI analysis path (Prompt 6) and photo quality checks
    # (Prompt 5): no background job queue exists in this project.
    result = ocr_provider.extract_invoice_data(file_bytes, get_settings())

    if not result.available:
        invoice.ocr_status = InvoiceOCRStatus.FAILED
        invoice.ocr_unavailable_reason = result.unavailable_reason
    else:
        invoice.ocr_status = InvoiceOCRStatus.COMPLETED
        invoice.ocr_raw_text = result.raw_text
        invoice.ocr_confidence = _map_confidence(result.confidence)
        invoice.extracted_amount = result.extracted_amount
        invoice.extracted_date = result.extracted_date
        invoice.extracted_vendor_name = result.extracted_vendor_name

    AuditLogger(db).log("INVOICE_UPLOADED", actor_id=farmer_id, actor_role="farmer", entity="invoice", entity_id=str(invoice.id))
    db.commit()
    db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


def _map_confidence(level: OCRConfidenceLevel | None) -> InvoiceOCRConfidence | None:
    if level is None:
        return None
    return InvoiceOCRConfidence(level.value)


def get_invoice(db: Session, farmer_id: str, invoice_id: uuid.UUID) -> InvoiceResponse:
    invoice = invoice_repository.get_owned(db, invoice_id, uuid.UUID(farmer_id))
    if invoice is None:
        raise AppError(error_codes.NOT_FOUND, "Invoice not found.", 404)
    return InvoiceResponse.model_validate(invoice)


def list_invoices(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> InvoiceListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
    invoices = invoice_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return InvoiceListResponse(items=[InvoiceResponse.model_validate(i) for i in invoices])


def confirm_invoice(db: Session, farmer_id: str, invoice_id: uuid.UUID, payload: InvoiceConfirmRequest) -> InvoiceResponse:
    """The ONLY function in this service that creates a real LedgerEntry
    - and only from the farmer's own typed-in values (payload), never
    from invoice.extracted_*, even if they happen to be identical."""
    farmer_uuid = uuid.UUID(farmer_id)
    invoice = invoice_repository.get_owned(db, invoice_id, farmer_uuid)
    if invoice is None:
        raise AppError(error_codes.NOT_FOUND, "Invoice not found.", 404)
    if invoice.is_confirmed:
        raise AppError(error_codes.VALIDATION_ERROR, "This invoice has already been confirmed.", 409)

    entry = LedgerEntry(
        farmer_id=farmer_uuid,
        crop_cycle_id=invoice.crop_cycle_id,
        entry_type=LedgerEntryType.EXPENSE,
        category=payload.category,
        amount=payload.amount,
        entry_date=payload.entry_date,
        description=f"Invoice: {payload.vendor_name}" if payload.vendor_name else "Invoice",
        source=LedgerEntrySource.INVOICE_LINKED,
    )
    ledger_entry_repository.create(db, entry)
    db.flush()

    invoice.is_confirmed = True
    invoice.confirmed_amount = payload.amount
    invoice.confirmed_date = payload.entry_date
    invoice.confirmed_vendor_name = payload.vendor_name
    invoice.confirmed_category = payload.category
    invoice.linked_ledger_entry_id = entry.id

    AuditLogger(db).log("INVOICE_CONFIRMED", actor_id=farmer_id, actor_role="farmer", entity="invoice", entity_id=str(invoice.id))
    db.commit()
    db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


def delete_invoice(db: Session, farmer_id: str, invoice_id: uuid.UUID, storage: FileStorage) -> None:
    invoice = invoice_repository.get_owned(db, invoice_id, uuid.UUID(farmer_id))
    if invoice is None:
        raise AppError(error_codes.NOT_FOUND, "Invoice not found.", 404)
    if invoice.is_confirmed:
        raise AppError(error_codes.VALIDATION_ERROR, "A confirmed invoice cannot be deleted - it is linked to a real ledger entry.", 409)

    try:
        storage.delete(invoice.image_storage_key)
    except Exception:
        pass

    invoice_repository.delete(db, invoice)
    AuditLogger(db).log("INVOICE_DELETED", actor_id=farmer_id, actor_role="farmer", entity="invoice", entity_id=str(invoice_id))
    db.commit()

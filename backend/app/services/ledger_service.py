"""
Ledger service. Manual entries are the primary mechanism; sale-import
reuses the real, existing SaleOrder.net_value verbatim - never
recomputed, adjusted, or estimated.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ledger_entry import LedgerCategory, LedgerEntry, LedgerEntrySource, LedgerEntryType
from app.repositories import crop_cycle_repository, ledger_entry_repository, sale_order_repository
from app.schemas.ledger import LedgerEntryCreateRequest, LedgerEntryResponse, LedgerImportSalesResponse, LedgerSummaryResponse
from app.services.audit_logger import AuditLogger


def create_manual_entry(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: LedgerEntryCreateRequest) -> LedgerEntryResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    entry = LedgerEntry(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        entry_type=payload.entry_type,
        category=payload.category,
        amount=payload.amount,
        entry_date=payload.entry_date,
        description=payload.description,
        source=LedgerEntrySource.MANUAL,
        crop_stage_definition_id=payload.crop_stage_definition_id,
    )
    ledger_entry_repository.create(db, entry)

    AuditLogger(db).log("LEDGER_ENTRY_CREATED", actor_id=farmer_id, actor_role="farmer", entity="ledger_entry", entity_id=str(entry.id))
    db.commit()
    db.refresh(entry)
    return LedgerEntryResponse.model_validate(entry)


def delete_entry(db: Session, farmer_id: str, entry_id: uuid.UUID) -> None:
    entry = ledger_entry_repository.get_owned(db, entry_id, uuid.UUID(farmer_id))
    if entry is None:
        raise AppError(error_codes.NOT_FOUND, "Ledger entry not found.", 404)
    if entry.source != LedgerEntrySource.MANUAL:
        raise AppError(error_codes.VALIDATION_ERROR, "Only manually-entered ledger entries can be deleted.", 409)

    ledger_entry_repository.delete(db, entry)
    AuditLogger(db).log("LEDGER_ENTRY_DELETED", actor_id=farmer_id, actor_role="farmer", entity="ledger_entry", entity_id=str(entry_id))
    db.commit()


def get_summary(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> LedgerSummaryResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    entries = ledger_entry_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    total_expense, total_revenue = ledger_entry_repository.compute_totals(db, crop_cycle_id, farmer_uuid)

    return LedgerSummaryResponse(
        crop_cycle_id=crop_cycle_id,
        total_expense=total_expense,
        total_revenue=total_revenue,
        net=total_revenue - total_expense,
        entries=[LedgerEntryResponse.model_validate(e) for e in entries],
    )


def import_completed_sales(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> LedgerImportSalesResponse:
    """Idempotent: a sale already imported (checked via the real DB
    unique constraint on linked_sale_id, and defensively re-checked here
    first) is never imported twice, and calling this repeatedly is always
    safe - it only ever adds entries for sales not yet reflected in the
    ledger."""
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    completed_sales = sale_order_repository.list_completed_sales_for_crop_cycle(db, crop_cycle_id, farmer_uuid)

    imported = []
    for sale in completed_sales:
        if ledger_entry_repository.get_by_linked_sale(db, sale.id) is not None:
            continue

        entry = LedgerEntry(
            farmer_id=farmer_uuid,
            crop_cycle_id=crop_cycle_id,
            entry_type=LedgerEntryType.REVENUE,
            category=LedgerCategory.HARVEST_SALE,
            amount=sale.net_value,
            entry_date=sale.completed_at.date() if sale.completed_at else sale.created_at.date(),
            description=f"Harvest sale ({sale.quantity} {sale.unit})",
            source=LedgerEntrySource.SALE_LINKED,
            linked_sale_id=sale.id,
        )
        ledger_entry_repository.create(db, entry)
        imported.append(entry)

    if imported:
        AuditLogger(db).log("LEDGER_SALES_IMPORTED", actor_id=farmer_id, actor_role="farmer", entity="crop_cycle", entity_id=str(crop_cycle_id))
        db.commit()
        for entry in imported:
            db.refresh(entry)

    return LedgerImportSalesResponse(imported_count=len(imported), entries=[LedgerEntryResponse.model_validate(e) for e in imported])

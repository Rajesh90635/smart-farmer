"""
D53-01/02/03/04/05/07, D52-04, D48-04 (docs/audit/FINAL_CANONICAL_group_C.md):
Storage domain - a farmer-owned physical storage facility, and the
episodes of harvest moved into/out of it. Mirrors harvest_service.py's
CRUD/ownership conventions. D52-04 (post-harvest) and D48-04 (pre-harvest
planning) are the same entity from a different workflow angle - no
separate code needed, per both rows' own text.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.storage import Storage
from app.models.storage_usage import StorageUsage
from app.repositories import harvest_repository, storage_repository
from app.schemas.storage import (
    StorageCreateRequest,
    StorageListResponse,
    StorageResponse,
    StorageUsageCreateRequest,
    StorageUsageListResponse,
    StorageUsageResponse,
)
from app.services.audit_logger import AuditLogger

_DEFAULT_PAGE_SIZE = 50


def create_storage(db: Session, farmer_id: str, payload: StorageCreateRequest) -> StorageResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    storage = Storage(
        farmer_id=farmer_uuid,
        location=payload.location,
        storage_type=payload.storage_type,
        capacity=payload.capacity,
        unit=payload.unit,
        cost_per_unit_per_day=payload.cost_per_unit_per_day,
    )
    storage_repository.create(db, storage)
    db.flush()

    AuditLogger(db).log("STORAGE_CREATED", actor_id=farmer_id, actor_role="farmer", entity="storage", entity_id=str(storage.id))
    db.commit()
    db.refresh(storage)
    return StorageResponse.model_validate(storage)


def list_my_storages(db: Session, farmer_id: str, *, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0) -> StorageListResponse:
    items, total = storage_repository.list_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return StorageListResponse(items=[StorageResponse.model_validate(i) for i in items], total=total)


def delete_storage(db: Session, farmer_id: str, storage_id: uuid.UUID) -> None:
    storage = storage_repository.get_owned(db, storage_id, uuid.UUID(farmer_id))
    if storage is None:
        raise AppError(error_codes.NOT_FOUND, "Storage not found.", 404)
    storage_repository.delete(db, storage)
    AuditLogger(db).log("STORAGE_DELETED", actor_id=farmer_id, actor_role="farmer", entity="storage", entity_id=str(storage_id))
    db.commit()


def _get_owned_storage_or_404(db: Session, farmer_id: str, storage_id: uuid.UUID) -> Storage:
    storage = storage_repository.get_owned(db, storage_id, uuid.UUID(farmer_id))
    if storage is None:
        raise AppError(error_codes.NOT_FOUND, "Storage not found.", 404)
    return storage


def record_storage_usage(
    db: Session, farmer_id: str, storage_id: uuid.UUID, payload: StorageUsageCreateRequest
) -> StorageUsageResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    _get_owned_storage_or_404(db, farmer_id, storage_id)

    # D53-04 (docs/audit/FINAL_CANONICAL_group_C.md): a harvest_record_id
    # must be a real harvest the farmer owns - never trusted merely
    # because it parses as a UUID, same discipline as every other
    # cross-entity reference in this project.
    harvest = harvest_repository.get_harvest_owned(db, payload.harvest_record_id, farmer_uuid)
    if harvest is None:
        raise AppError(error_codes.NOT_FOUND, "Harvest record not found.", 404)

    usage = StorageUsage(
        storage_id=storage_id,
        harvest_record_id=payload.harvest_record_id,
        farmer_id=farmer_uuid,
        quantity=payload.quantity,
        unit=payload.unit,
    )
    storage_repository.create_usage(db, usage)
    db.flush()

    AuditLogger(db).log("STORAGE_USAGE_RECORDED", actor_id=farmer_id, actor_role="farmer", entity="storage_usage", entity_id=str(usage.id))
    db.commit()
    db.refresh(usage)
    return StorageUsageResponse.model_validate(usage)


def list_storage_usages(
    db: Session, farmer_id: str, storage_id: uuid.UUID, *, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0
) -> StorageUsageListResponse:
    _get_owned_storage_or_404(db, farmer_id, storage_id)
    items, total = storage_repository.list_usages_for_storage(db, storage_id, limit=limit, offset=offset)
    return StorageUsageListResponse(items=[StorageUsageResponse.model_validate(i) for i in items], total=total)


def release_storage_usage(db: Session, farmer_id: str, storage_id: uuid.UUID, usage_id: uuid.UUID) -> StorageUsageResponse:
    """D53-07: sets released_at once. Idempotent - a second call returns
    the original release timestamp unchanged rather than overwriting it,
    same convention as case_service.acknowledge_review (D36-04)."""
    _get_owned_storage_or_404(db, farmer_id, storage_id)
    usage = storage_repository.get_usage_owned(db, usage_id, storage_id, uuid.UUID(farmer_id))
    if usage is None:
        raise AppError(error_codes.NOT_FOUND, "Storage usage record not found.", 404)

    if usage.released_at is None:
        usage.released_at = datetime.now(timezone.utc)
        AuditLogger(db).log("STORAGE_USAGE_RELEASED", actor_id=farmer_id, actor_role="farmer", entity="storage_usage", entity_id=str(usage_id))
        db.commit()
        db.refresh(usage)
    return StorageUsageResponse.model_validate(usage)

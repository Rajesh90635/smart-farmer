"""D53-01/02/03/04/05/07 (docs/audit/FINAL_CANONICAL_group_C.md): storage
facility management + storage-usage (moving a harvest into/out of
storage) endpoints."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.storage import (
    StorageCreateRequest,
    StorageListResponse,
    StorageResponse,
    StorageUsageCreateRequest,
    StorageUsageListResponse,
    StorageUsageResponse,
)
from app.services import storage_service

router = APIRouter(prefix="/storages", tags=["storage"])


@router.post("", response_model=StorageResponse, status_code=status.HTTP_201_CREATED)
def create_storage(
    payload: StorageCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> StorageResponse:
    return storage_service.create_storage(db, current_user.user_id, payload)


@router.get("", response_model=StorageListResponse)
def list_my_storages(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> StorageListResponse:
    return storage_service.list_my_storages(db, current_user.user_id, limit=limit, offset=offset)


@router.delete("/{storage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storage(
    storage_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    storage_service.delete_storage(db, current_user.user_id, storage_id)


@router.post("/{storage_id}/usages", response_model=StorageUsageResponse, status_code=status.HTTP_201_CREATED)
def record_storage_usage(
    storage_id: uuid.UUID,
    payload: StorageUsageCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> StorageUsageResponse:
    return storage_service.record_storage_usage(db, current_user.user_id, storage_id, payload)


@router.get("/{storage_id}/usages", response_model=StorageUsageListResponse)
def list_storage_usages(
    storage_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> StorageUsageListResponse:
    return storage_service.list_storage_usages(db, current_user.user_id, storage_id, limit=limit, offset=offset)


@router.post("/{storage_id}/usages/{usage_id}/release", response_model=StorageUsageResponse)
def release_storage_usage(
    storage_id: uuid.UUID,
    usage_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> StorageUsageResponse:
    return storage_service.release_storage_usage(db, current_user.user_id, storage_id, usage_id)

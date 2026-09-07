import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.storage import Storage
from app.models.storage_usage import StorageUsage


def create(db: Session, storage: Storage) -> Storage:
    db.add(storage)
    return storage


def get_owned(db: Session, storage_id: uuid.UUID, farmer_id: uuid.UUID) -> Storage | None:
    return db.execute(select(Storage).where(Storage.id == storage_id, Storage.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[Storage], int]:
    stmt = select(Storage).where(Storage.farmer_id == farmer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(Storage.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def delete(db: Session, storage: Storage) -> None:
    db.execute(sa_delete(Storage).where(Storage.id == storage.id))


def create_usage(db: Session, usage: StorageUsage) -> StorageUsage:
    db.add(usage)
    return usage


def get_usage_owned(db: Session, usage_id: uuid.UUID, storage_id: uuid.UUID, farmer_id: uuid.UUID) -> StorageUsage | None:
    return db.execute(
        select(StorageUsage).where(StorageUsage.id == usage_id, StorageUsage.storage_id == storage_id, StorageUsage.farmer_id == farmer_id)
    ).scalar_one_or_none()


def list_usages_for_storage(db: Session, storage_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[StorageUsage], int]:
    stmt = select(StorageUsage).where(StorageUsage.storage_id == storage_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(StorageUsage.stored_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total

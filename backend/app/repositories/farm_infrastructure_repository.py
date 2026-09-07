"""FarmInfrastructure repository. Ownership enforced the same way as
every other farm-scoped entity in this project."""
import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.farm_infrastructure import FarmInfrastructure


def create(db: Session, item: FarmInfrastructure) -> FarmInfrastructure:
    db.add(item)
    return item


def get_owned(db: Session, item_id: uuid.UUID, farm_id: uuid.UUID) -> FarmInfrastructure | None:
    return db.execute(
        select(FarmInfrastructure).where(FarmInfrastructure.id == item_id, FarmInfrastructure.farm_id == farm_id)
    ).scalar_one_or_none()


def list_for_farm(db: Session, farm_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[FarmInfrastructure], int]:
    base = select(FarmInfrastructure).where(FarmInfrastructure.farm_id == farm_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = db.execute(base.order_by(FarmInfrastructure.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def delete(db: Session, item: FarmInfrastructure) -> None:
    db.execute(sa_delete(FarmInfrastructure).where(FarmInfrastructure.id == item.id))

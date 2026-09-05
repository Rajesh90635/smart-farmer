import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.farm import Farm, FarmStatus


def create(db: Session, farm: Farm) -> Farm:
    db.add(farm)
    return farm


def get_owned(db: Session, farm_id: uuid.UUID, farmer_id: uuid.UUID) -> Farm | None:
    """Returns the farm only if it belongs to farmer_id - the ownership
    check lives here, in the one place every farm lookup goes through,
    rather than being re-implemented (and possibly forgotten) at each
    call site."""
    return db.execute(
        select(Farm).where(Farm.id == farm_id, Farm.farmer_id == farmer_id)
    ).scalar_one_or_none()


def list_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[Farm], int]:
    base = select(Farm).where(Farm.farmer_id == farmer_id, Farm.status == FarmStatus.ACTIVE)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = db.execute(base.order_by(Farm.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def count_active_for_farmer(db: Session, farmer_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count()).select_from(Farm).where(Farm.farmer_id == farmer_id, Farm.status == FarmStatus.ACTIVE)
    ).scalar_one()


def list_active_with_location(db: Session, *, farm_ids: list[uuid.UUID] | None = None) -> list[Farm]:
    """D16-10 (docs/audit/c03_weather_water_soil.md) - used by the
    proactive weather-alert sweep (weather_alert_orchestration_service.py)
    to check every farm with a location, not just ones a farmer happens
    to open the weather screen for. `farm_ids` narrows to a specific set
    (a targeted manual re-run, or a test) - omitted, the real scheduled
    job sweeps every eligible farm."""
    conditions = [Farm.status == FarmStatus.ACTIVE, Farm.latitude.isnot(None), Farm.longitude.isnot(None)]
    if farm_ids is not None:
        conditions.append(Farm.id.in_(farm_ids))
    return list(db.execute(select(Farm).where(*conditions)).scalars().all())

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.farm import Farm, FarmStatus
from app.models.plot import Plot


def create(db: Session, plot: Plot) -> Plot:
    db.add(plot)
    return plot


def get_owned(db: Session, plot_id: uuid.UUID, farmer_id: uuid.UUID) -> Plot | None:
    """A plot has no farmer_id of its own - ownership is via its parent
    Farm, so this always joins through Farm rather than trusting a
    plot_id alone. This is the single choke point for plot ownership
    enforcement."""
    return db.execute(
        select(Plot)
        .join(Farm, Plot.farm_id == Farm.id)
        .where(Plot.id == plot_id, Farm.farmer_id == farmer_id)
        .options(joinedload(Plot.farm))
    ).unique().scalar_one_or_none()


def list_for_farm(db: Session, farm_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[Plot], int]:
    base = select(Plot).where(Plot.farm_id == farm_id, Plot.status == FarmStatus.ACTIVE)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = db.execute(base.order_by(Plot.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def count_active_for_farmer(db: Session, farmer_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count())
        .select_from(Plot)
        .join(Farm, Plot.farm_id == Farm.id)
        .where(Farm.farmer_id == farmer_id, Plot.status == FarmStatus.ACTIVE)
    ).scalar_one()


def sum_area_sqm_for_farm(db: Session, farm_id: uuid.UUID) -> Decimal | None:
    """D71-06 (docs/audit/FINAL_CANONICAL_group_C.md): the farm's current
    land area for the per-acre P&L figures - active plots only, same
    scope as list_for_farm above. None (not 0) when the farm has no
    active plot at all, so a per-acre figure is never fabricated as 0
    rather than genuinely unavailable."""
    has_any = db.execute(
        select(Plot.id).where(Plot.farm_id == farm_id, Plot.status == FarmStatus.ACTIVE).limit(1)
    ).scalar_one_or_none()
    if has_any is None:
        return None
    total = db.execute(
        select(func.coalesce(func.sum(Plot.area_sqm), 0)).where(Plot.farm_id == farm_id, Plot.status == FarmStatus.ACTIVE)
    ).scalar_one()
    return Decimal(total)

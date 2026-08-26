import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.crop_cycle import CropCycle, CultivationStatus
from app.models.farm import Farm
from app.models.plot import Plot

_TERMINAL_STATUSES = (CultivationStatus.HARVESTED, CultivationStatus.CANCELLED)


def create(db: Session, crop_cycle: CropCycle) -> CropCycle:
    db.add(crop_cycle)
    return crop_cycle


def get_owned(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> CropCycle | None:
    """Ownership for a crop cycle is two joins away (CropCycle -> Plot ->
    Farm.farmer_id) - always enforced here, never left to the caller to
    remember."""
    return (
        db.execute(
            select(CropCycle)
            .join(Plot, CropCycle.plot_id == Plot.id)
            .join(Farm, Plot.farm_id == Farm.id)
            .where(CropCycle.id == crop_cycle_id, Farm.farmer_id == farmer_id)
            .options(joinedload(CropCycle.crop), joinedload(CropCycle.plot))
        )
        .unique()
        .scalar_one_or_none()
    )


def list_for_plot(db: Session, plot_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[CropCycle], int]:
    base = select(CropCycle).where(CropCycle.plot_id == plot_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = (
        db.execute(
            base.options(joinedload(CropCycle.crop))
            .order_by(CropCycle.sowing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .scalars()
        .all()
    )
    return list(items), total


def list_all_for_farmer(db: Session, farmer_id: uuid.UUID) -> list[CropCycle]:
    """Added Phase 39 (Personalization) - no existing function listed
    ALL of a farmer's crop cycles across every plot/farm; only
    plot-scoped or nearing-harvest-filtered variants existed. Joins
    through the real, existing Plot -> Farm chain (unchanged), never a
    new relationship. `.crop` is eager-loaded so this is also safe to
    serialize directly as CropCycleResponse (needed by the farmer-wide
    GET /crops listing added for the Camera tab's crop picker) without
    an extra query per row."""
    return list(
        db.execute(
            select(CropCycle)
            .join(Plot, CropCycle.plot_id == Plot.id)
            .join(Farm, Plot.farm_id == Farm.id)
            .where(Farm.farmer_id == farmer_id)
            .options(joinedload(CropCycle.crop))
            .order_by(CropCycle.sowing_date.desc())
        )
        .unique()
        .scalars()
        .all()
    )


def count_active_for_farmer(db: Session, farmer_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count())
        .select_from(CropCycle)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .join(Farm, Plot.farm_id == Farm.id)
        .where(Farm.farmer_id == farmer_id, CropCycle.cultivation_status.notin_(_TERMINAL_STATUSES))
    ).scalar_one()


def list_nearing_harvest_for_farmer(db: Session, farmer_id: uuid.UUID, *, within_days: int, limit: int) -> list[CropCycle]:
    today = date.today()
    horizon = today + timedelta(days=within_days)
    stmt = (
        select(CropCycle)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .join(Farm, Plot.farm_id == Farm.id)
        .where(
            Farm.farmer_id == farmer_id,
            CropCycle.cultivation_status.notin_(_TERMINAL_STATUSES),
            CropCycle.expected_harvest_date.is_not(None),
            CropCycle.expected_harvest_date <= horizon,
            CropCycle.expected_harvest_date >= today,
        )
        .options(joinedload(CropCycle.crop))
        .order_by(CropCycle.expected_harvest_date.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).unique().scalars().all())

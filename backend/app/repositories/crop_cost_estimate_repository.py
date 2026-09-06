"""
CropCostEstimate repository. Ownership enforced the same way as every
other farmer-scoped entity in this project.
"""
import uuid
from decimal import Decimal

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.crop_cost_estimate import CropCostEstimate
from app.models.crop_cycle import CropCycle, Season
from app.models.plot import Plot


def create(db: Session, estimate: CropCostEstimate) -> CropCostEstimate:
    db.add(estimate)
    return estimate


def get_owned(db: Session, estimate_id: uuid.UUID, farmer_id: uuid.UUID) -> CropCostEstimate | None:
    return db.execute(select(CropCostEstimate).where(CropCostEstimate.id == estimate_id, CropCostEstimate.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[CropCostEstimate]:
    return list(
        db.execute(
            select(CropCostEstimate)
            .where(CropCostEstimate.crop_cycle_id == crop_cycle_id, CropCostEstimate.farmer_id == farmer_id)
            .order_by(CropCostEstimate.created_at.desc())
        )
        .scalars()
        .all()
    )


def total_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> Decimal | None:
    """Returns None (not zero) when there are genuinely no estimate rows
    at all - "no estimate entered yet" and "estimated at zero" are
    different facts and must never be conflated."""
    has_any = db.execute(
        select(CropCostEstimate.id).where(CropCostEstimate.crop_cycle_id == crop_cycle_id, CropCostEstimate.farmer_id == farmer_id).limit(1)
    ).scalar_one_or_none()
    if has_any is None:
        return None
    total = db.execute(
        select(func.coalesce(func.sum(CropCostEstimate.estimated_amount), 0)).where(
            CropCostEstimate.crop_cycle_id == crop_cycle_id, CropCostEstimate.farmer_id == farmer_id
        )
    ).scalar_one()
    return Decimal(total)


def total_for_plot(db: Session, plot_id: uuid.UUID, farmer_id: uuid.UUID) -> Decimal | None:
    """D71-05 (docs/audit/FINAL_CANONICAL_group_C.md): same None-vs-zero
    discipline as total_for_crop_cycle above, joined out to every crop
    cycle this plot has ever had."""
    has_any = db.execute(
        select(CropCostEstimate.id)
        .join(CropCycle, CropCostEstimate.crop_cycle_id == CropCycle.id)
        .where(CropCycle.plot_id == plot_id, CropCostEstimate.farmer_id == farmer_id)
        .limit(1)
    ).scalar_one_or_none()
    if has_any is None:
        return None
    total = db.execute(
        select(func.coalesce(func.sum(CropCostEstimate.estimated_amount), 0))
        .join(CropCycle, CropCostEstimate.crop_cycle_id == CropCycle.id)
        .where(CropCycle.plot_id == plot_id, CropCostEstimate.farmer_id == farmer_id)
    ).scalar_one()
    return Decimal(total)


def total_for_farm(db: Session, farm_id: uuid.UUID, farmer_id: uuid.UUID) -> Decimal | None:
    """D71-06: same pattern as total_for_plot, one level up via Plot.farm_id."""
    has_any = db.execute(
        select(CropCostEstimate.id)
        .join(CropCycle, CropCostEstimate.crop_cycle_id == CropCycle.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .where(Plot.farm_id == farm_id, CropCostEstimate.farmer_id == farmer_id)
        .limit(1)
    ).scalar_one_or_none()
    if has_any is None:
        return None
    total = db.execute(
        select(func.coalesce(func.sum(CropCostEstimate.estimated_amount), 0))
        .join(CropCycle, CropCostEstimate.crop_cycle_id == CropCycle.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .where(Plot.farm_id == farm_id, CropCostEstimate.farmer_id == farmer_id)
    ).scalar_one()
    return Decimal(total)


def total_for_season(db: Session, farmer_id: uuid.UUID, season: Season) -> Decimal | None:
    """D71-07: same pattern as total_for_plot, scoped by Season across
    every one of the farmer's own crop cycles."""
    has_any = db.execute(
        select(CropCostEstimate.id)
        .join(CropCycle, CropCostEstimate.crop_cycle_id == CropCycle.id)
        .where(CropCycle.season == season, CropCostEstimate.farmer_id == farmer_id)
        .limit(1)
    ).scalar_one_or_none()
    if has_any is None:
        return None
    total = db.execute(
        select(func.coalesce(func.sum(CropCostEstimate.estimated_amount), 0))
        .join(CropCycle, CropCostEstimate.crop_cycle_id == CropCycle.id)
        .where(CropCycle.season == season, CropCostEstimate.farmer_id == farmer_id)
    ).scalar_one()
    return Decimal(total)


def delete(db: Session, estimate: CropCostEstimate) -> None:
    db.execute(sa_delete(CropCostEstimate).where(CropCostEstimate.id == estimate.id))

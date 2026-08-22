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


def delete(db: Session, estimate: CropCostEstimate) -> None:
    db.execute(sa_delete(CropCostEstimate).where(CropCostEstimate.id == estimate.id))

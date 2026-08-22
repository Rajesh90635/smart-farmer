"""
Advisory feedback repository. Ownership enforced the same way as every
other farmer-scoped entity in this project.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.advisory_feedback import AdvisoryFeedback


def create(db: Session, feedback: AdvisoryFeedback) -> AdvisoryFeedback:
    db.add(feedback)
    return feedback


def list_for_farmer(db: Session, farmer_id: uuid.UUID) -> list[AdvisoryFeedback]:
    return list(db.execute(select(AdvisoryFeedback).where(AdvisoryFeedback.farmer_id == farmer_id)).scalars().all())


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[AdvisoryFeedback]:
    return list(
        db.execute(
            select(AdvisoryFeedback).where(AdvisoryFeedback.crop_cycle_id == crop_cycle_id, AdvisoryFeedback.farmer_id == farmer_id)
        )
        .scalars()
        .all()
    )

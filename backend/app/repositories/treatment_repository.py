"""
Treatment/follow-up repositories. Ownership enforced the same way as
every other farmer-scoped entity in this project.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.treatment_follow_up import TreatmentFollowUp
from app.models.treatment_record import TreatmentRecord


def create_treatment(db: Session, treatment: TreatmentRecord) -> TreatmentRecord:
    db.add(treatment)
    return treatment


def get_treatment_owned(db: Session, treatment_id: uuid.UUID, farmer_id: uuid.UUID) -> TreatmentRecord | None:
    return db.execute(select(TreatmentRecord).where(TreatmentRecord.id == treatment_id, TreatmentRecord.farmer_id == farmer_id)).scalar_one_or_none()


def list_treatments_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[TreatmentRecord]:
    return list(
        db.execute(
            select(TreatmentRecord)
            .where(TreatmentRecord.crop_cycle_id == crop_cycle_id, TreatmentRecord.farmer_id == farmer_id)
            .order_by(TreatmentRecord.application_date.desc())
        )
        .scalars()
        .all()
    )


def create_follow_up(db: Session, follow_up: TreatmentFollowUp) -> TreatmentFollowUp:
    db.add(follow_up)
    return follow_up


def get_follow_up_owned(db: Session, follow_up_id: uuid.UUID, farmer_id: uuid.UUID) -> TreatmentFollowUp | None:
    return db.execute(
        select(TreatmentFollowUp).where(TreatmentFollowUp.id == follow_up_id, TreatmentFollowUp.farmer_id == farmer_id)
    ).scalar_one_or_none()


def list_follow_ups_for_treatment(db: Session, treatment_id: uuid.UUID, farmer_id: uuid.UUID) -> list[TreatmentFollowUp]:
    return list(
        db.execute(
            select(TreatmentFollowUp)
            .where(TreatmentFollowUp.treatment_id == treatment_id, TreatmentFollowUp.farmer_id == farmer_id)
            .order_by(TreatmentFollowUp.observation_date.desc())
        )
        .scalars()
        .all()
    )

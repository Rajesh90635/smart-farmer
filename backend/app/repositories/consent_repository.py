import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consent_record import ConsentRecord, ConsentType


def list_for_user(db: Session, user_id: uuid.UUID) -> list[ConsentRecord]:
    return list(
        db.execute(select(ConsentRecord).where(ConsentRecord.user_id == user_id).order_by(ConsentRecord.recorded_at))
        .scalars()
        .all()
    )


def get_latest(db: Session, user_id: uuid.UUID, consent_type: ConsentType) -> ConsentRecord | None:
    return db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id, ConsentRecord.consent_type == consent_type)
        .order_by(ConsentRecord.recorded_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def create(db: Session, record: ConsentRecord) -> ConsentRecord:
    db.add(record)
    return record

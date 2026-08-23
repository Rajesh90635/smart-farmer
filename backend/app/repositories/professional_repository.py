import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.professional_profile import ProfessionalProfile, VerificationStatus
from app.models.verification_record import VerificationRecord


def create(db: Session, profile: ProfessionalProfile) -> ProfessionalProfile:
    db.add(profile)
    return profile


def get_by_user_id(db: Session, user_id: uuid.UUID) -> ProfessionalProfile | None:
    return db.execute(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)).scalar_one_or_none()


def get_by_id(db: Session, professional_id: uuid.UUID) -> ProfessionalProfile | None:
    return db.get(ProfessionalProfile, professional_id)


def list_verified_by_role(db: Session, role: str, *, limit: int, offset: int) -> tuple[list[ProfessionalProfile], int]:
    base = select(ProfessionalProfile).where(ProfessionalProfile.role == role, ProfessionalProfile.verification_status == VerificationStatus.VERIFIED)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = db.execute(base.order_by(ProfessionalProfile.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def candidates_for_matching(db: Session, role: str) -> list[ProfessionalProfile]:
    """All VERIFIED candidates for a role - full ranking/filtering
    (service area, expertise, language, availability, workload) happens in
    the matching service, not here; this just narrows to professionals who
    could possibly ever receive a case at all."""
    return list(
        db.execute(
            select(ProfessionalProfile).where(
                ProfessionalProfile.role == role,
                ProfessionalProfile.verification_status == VerificationStatus.VERIFIED,
            )
        ).scalars().all()
    )


def create_verification_record(db: Session, record: VerificationRecord) -> VerificationRecord:
    db.add(record)
    return record


def list_verification_history(db: Session, professional_id: uuid.UUID) -> list[VerificationRecord]:
    return list(
        db.execute(
            select(VerificationRecord).where(VerificationRecord.professional_id == professional_id).order_by(VerificationRecord.created_at.desc())
        ).scalars().all()
    )

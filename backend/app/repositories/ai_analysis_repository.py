import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.ai_analysis import AIAnalysis, ResultStatus
from app.models.ai_analysis_session import AIAnalysisSession
from app.models.crop_photo import CropPhoto


def create_session(db: Session, session_obj: AIAnalysisSession) -> AIAnalysisSession:
    db.add(session_obj)
    return session_obj


def get_session_owned(db: Session, session_id: uuid.UUID, farmer_id: uuid.UUID) -> AIAnalysisSession | None:
    return db.execute(
        select(AIAnalysisSession).where(AIAnalysisSession.id == session_id, AIAnalysisSession.farmer_id == farmer_id)
    ).scalar_one_or_none()


def create_analysis(db: Session, analysis: AIAnalysis) -> AIAnalysis:
    db.add(analysis)
    return analysis


def get_analysis_owned(db: Session, analysis_id: uuid.UUID, farmer_id: uuid.UUID) -> AIAnalysis | None:
    return db.execute(
        select(AIAnalysis).where(AIAnalysis.id == analysis_id, AIAnalysis.farmer_id == farmer_id)
    ).scalar_one_or_none()


def get_latest_for_photo(db: Session, crop_photo_id: uuid.UUID, farmer_id: uuid.UUID) -> AIAnalysis | None:
    return db.execute(
        select(AIAnalysis)
        .where(AIAnalysis.crop_photo_id == crop_photo_id, AIAnalysis.farmer_id == farmer_id)
        .order_by(AIAnalysis.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_in_flight_for_photo(db: Session, crop_photo_id: uuid.UUID, farmer_id: uuid.UUID) -> AIAnalysis | None:
    """An analysis that's still PENDING/PROCESSING for this exact photo -
    used to make a duplicate analyze request a no-op (return the existing
    in-flight job) rather than starting a second, redundant one."""
    from app.models.ai_analysis import AnalysisStatus

    return db.execute(
        select(AIAnalysis).where(
            AIAnalysis.crop_photo_id == crop_photo_id,
            AIAnalysis.farmer_id == farmer_id,
            AIAnalysis.analysis_status.in_([AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]),
        )
    ).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[AIAnalysis]:
    return list(
        db.execute(
            select(AIAnalysis)
            .where(AIAnalysis.crop_cycle_id == crop_cycle_id, AIAnalysis.farmer_id == farmer_id)
            .order_by(AIAnalysis.created_at.desc())
        ).scalars().all()
    )


def list_for_session(db: Session, session_id: uuid.UUID) -> list[AIAnalysis]:
    return list(
        db.execute(select(AIAnalysis).where(AIAnalysis.analysis_session_id == session_id).order_by(AIAnalysis.created_at.asc()))
        .scalars()
        .all()
    )


def count_by_result_status(db: Session, result_status: ResultStatus) -> int:
    """D91-09/D91-10 (docs/audit/FINAL_CANONICAL_group_D.md): the real
    denominator a false-positive/false-negative RATE needs - every
    analysis of that result type, not just the ones a farmer corrected."""
    return db.execute(select(func.count()).select_from(AIAnalysis).where(AIAnalysis.result_status == result_status)).scalar_one()


def count_by_result_status_and_correction(db: Session, result_status: ResultStatus, correction: str) -> int:
    return db.execute(
        select(func.count()).select_from(AIAnalysis).where(
            AIAnalysis.result_status == result_status, AIAnalysis.farmer_correction == correction
        )
    ).scalar_one()


def count_by_correction(db: Session, correction: str) -> int:
    return db.execute(select(func.count()).select_from(AIAnalysis).where(AIAnalysis.farmer_correction == correction)).scalar_one()

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_model_registry import AIModelRegistry
from app.models.crop_stage_definition import CropStageDefinition
from app.models.disease_class import DiseaseClass


def get_active_model(db: Session) -> AIModelRegistry | None:
    return db.execute(select(AIModelRegistry).where(AIModelRegistry.is_active.is_(True))).scalar_one_or_none()


def get_fallback_not_configured_model(db: Session) -> AIModelRegistry | None:
    """The seeded placeholder row representing 'no real model configured' -
    used when there is no active model, so every AIAnalysis still points
    at a real registry row rather than a magic string."""
    return db.execute(
        select(AIModelRegistry).where(AIModelRegistry.name == "crop_disease_baseline", AIModelRegistry.version == "unconfigured-0.0")
    ).scalar_one_or_none()


def list_diseases_for_crop(db: Session, crop_id: uuid.UUID) -> list[DiseaseClass]:
    return list(
        db.execute(
            select(DiseaseClass).where(DiseaseClass.crop_id == crop_id, DiseaseClass.is_active.is_(True)).order_by(DiseaseClass.disease_name)
        ).scalars().all()
    )


def list_stages_for_crop(db: Session, crop_id: uuid.UUID) -> list[CropStageDefinition]:
    return list(
        db.execute(
            select(CropStageDefinition)
            .where(CropStageDefinition.crop_id == crop_id, CropStageDefinition.is_active.is_(True))
            .order_by(CropStageDefinition.sequence_order)
        ).scalars().all()
    )

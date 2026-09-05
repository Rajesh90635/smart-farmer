"""
AI analysis orchestration.

Async-processing note (Requirement 23): the PENDING -> PROCESSING ->
COMPLETED/FAILED state machine is real and is exactly what a genuine
background worker (Celery/RQ/etc.) would drive later. In THIS phase, the
"processing" step runs synchronously within the same request, immediately
after the PENDING row is committed - because the only real work being done
right now is a `NotConfiguredModelProvider` call with zero actual
computation cost. Introducing a real task queue for genuinely free work
would be exactly the "complicated distributed architecture" the spec says
not to build yet. When a real model with real inference cost is
integrated, `_run_analysis` is the one function that moves behind a queue
- no endpoint or schema changes needed.
"""
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.ai_analysis import AIAnalysis, AnalysisStatus, ResultStatus
from app.models.crop_photo import ImageQualityStatus
from app.repositories import ai_analysis_repository, ai_reference_repository, crop_cycle_repository, crop_photo_repository
from app.schemas.ai_analysis import AIAnalysisCorrectionRequest, AIAnalysisListResponse, AIAnalysisResponse
from app.services.ai.model_provider import ModelProvider
from app.services.ai.prediction_validator import validate_disease_prediction
from app.services.audit_logger import AuditLogger
from app.services.storage.base import FileStorage


def analyze_photo(
    db: Session,
    farmer_id: str,
    photo_id: uuid.UUID,
    model_provider: ModelProvider,
    storage: FileStorage,
    settings: Settings,
    analysis_session_id: uuid.UUID | None = None,
) -> AIAnalysisResponse:
    farmer_uuid = uuid.UUID(farmer_id)

    photo = crop_photo_repository.get_owned(db, photo_id, farmer_uuid)
    if photo is None:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)

    # Duplicate-request handling: if an analysis is already in flight for
    # this exact photo, return it rather than starting a redundant job.
    in_flight = ai_analysis_repository.get_in_flight_for_photo(db, photo_id, farmer_uuid)
    if in_flight is not None:
        return AIAnalysisResponse.model_validate(in_flight)

    # The quality gate is a hard stop BEFORE any inference attempt -
    # reusing Prompt 5's quality verdict, not re-checking it.
    if photo.image_quality_status == ImageQualityStatus.REJECTED:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            "This photo's quality was flagged as insufficient. Please take a clearer photo before analyzing.",
            422,
        )

    crop_cycle = crop_cycle_repository.get_owned(db, photo.crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    model_row = ai_reference_repository.get_active_model(db) or ai_reference_repository.get_fallback_not_configured_model(db)
    if model_row is None:
        raise AppError("MODEL_REGISTRY_EMPTY", "No AI model is registered in this environment.", 500)

    analysis = AIAnalysis(
        crop_photo_id=photo.id,
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle.id,
        crop_id=crop_cycle.crop_id,
        model_registry_id=model_row.id,
        model_name=model_row.name,
        model_version=model_row.version,
        result_status=ResultStatus.PROCESSING,
        analysis_status=AnalysisStatus.PENDING,
        requires_review=True,
        preprocessing_version="v1",
        analysis_session_id=analysis_session_id,
    )
    ai_analysis_repository.create_analysis(db, analysis)
    db.flush()

    AuditLogger(db).log(
        "AI_ANALYSIS_REQUESTED", actor_id=farmer_id, actor_role="farmer", entity="ai_analysis", entity_id=str(analysis.id)
    )
    db.commit()
    db.refresh(analysis)

    _run_analysis(db, analysis, photo, crop_cycle.crop.name, model_provider, storage, settings)

    db.refresh(analysis)
    return AIAnalysisResponse.model_validate(analysis)


def _run_analysis(
    db: Session, analysis: AIAnalysis, photo, crop_name: str, model_provider: ModelProvider, storage: FileStorage, settings: Settings
) -> None:
    analysis.analysis_status = AnalysisStatus.PROCESSING
    db.commit()

    start = time.monotonic()
    try:
        with storage.open_read(photo.storage_key) as f:
            image_bytes = f.read()

        prediction = model_provider.predict_disease(image_bytes, crop_name)
        safe_result = validate_disease_prediction(
            prediction,
            crop_name=crop_name,
            supported_crop_names=model_provider.supported_crop_names(),
            settings=settings,
        )

        analysis.result_status = safe_result.result_status
        analysis.predicted_class = safe_result.predicted_class
        analysis.confidence = safe_result.confidence
        analysis.requires_review = safe_result.requires_review
        analysis.top_k_predictions = safe_result.top_k_predictions
        analysis.analysis_status = AnalysisStatus.COMPLETED
        analysis.inference_timestamp = datetime.now(timezone.utc)

    except Exception:  # noqa: BLE001 - any failure must degrade to a safe, honest FAILED state, never a fabricated result or an unhandled 500
        analysis.result_status = ResultStatus.FAILED
        analysis.analysis_status = AnalysisStatus.FAILED
        analysis.requires_review = True

    analysis.processing_time_ms = int((time.monotonic() - start) * 1000)
    db.commit()


def get_analysis(db: Session, farmer_id: str, analysis_id: uuid.UUID) -> AIAnalysisResponse:
    analysis = ai_analysis_repository.get_analysis_owned(db, analysis_id, uuid.UUID(farmer_id))
    if analysis is None:
        raise AppError(error_codes.NOT_FOUND, "Analysis not found.", 404)
    return AIAnalysisResponse.model_validate(analysis)


def submit_correction(db: Session, farmer_id: str, analysis_id: uuid.UUID, payload: AIAnalysisCorrectionRequest) -> AIAnalysisResponse:
    """D91-07 (docs/audit/c13_governance_farmbrain_security.md): a
    farmer's own after-the-fact correction of THIS specific AI result -
    distinct from AdvisoryFeedback, which never covered the disease
    pipeline. Also the raw false-positive/false-negative signal D91-09/
    D91-10 need. Overwritable (a farmer can change their mind), not
    append-only - AuditLogger still records every submission."""
    analysis = ai_analysis_repository.get_analysis_owned(db, analysis_id, uuid.UUID(farmer_id))
    if analysis is None:
        raise AppError(error_codes.NOT_FOUND, "Analysis not found.", 404)

    analysis.farmer_correction = payload.correction.value
    analysis.farmer_correction_notes = payload.notes
    analysis.farmer_corrected_at = datetime.now(timezone.utc)

    AuditLogger(db).log(
        "AI_ANALYSIS_FARMER_CORRECTION_SUBMITTED", actor_id=farmer_id, actor_role="farmer",
        entity="ai_analysis", entity_id=str(analysis.id),
    )
    db.commit()
    db.refresh(analysis)
    return AIAnalysisResponse.model_validate(analysis)


def get_latest_for_photo(db: Session, farmer_id: str, photo_id: uuid.UUID) -> AIAnalysisResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    photo = crop_photo_repository.get_owned(db, photo_id, farmer_uuid)
    if photo is None:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)

    analysis = ai_analysis_repository.get_latest_for_photo(db, photo_id, farmer_uuid)
    if analysis is None:
        raise AppError(error_codes.NOT_FOUND, "No analysis found for this photo yet.", 404)
    return AIAnalysisResponse.model_validate(analysis)


def list_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> AIAnalysisListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return AIAnalysisListResponse(items=[AIAnalysisResponse.model_validate(a) for a in analyses], total=len(analyses))

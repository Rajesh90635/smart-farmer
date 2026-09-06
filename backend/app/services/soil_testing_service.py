"""
D20-01/02 (docs/audit/FINAL_CANONICAL_group_A.md): Soil Testing domain
foundation - previously entirely missing (confirmed by exhaustive search
for soil_sample/soil_test across app/ and tests/ before this session).
"""
import io
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.notification import NotificationCategory, NotificationPriority
from app.models.soil_sample import SoilSample
from app.models.soil_test_result import SoilTestResult
from app.repositories import plot_repository, soil_testing_repository, user_repository
from app.schemas.soil_testing import (
    SoilSampleCreateRequest,
    SoilSampleListResponse,
    SoilSampleResponse,
    SoilTestResultCreateRequest,
    SoilTestResultListResponse,
    SoilTestResultResponse,
)
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.storage.base import FileStorage
from app.services.weather_alert_rules import AlertCandidate


def create_soil_sample(db: Session, farmer_id: str, plot_id: uuid.UUID, payload: SoilSampleCreateRequest) -> SoilSampleResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    plot = plot_repository.get_owned(db, plot_id, farmer_uuid)
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)

    sample = SoilSample(
        farmer_id=farmer_uuid, plot_id=plot_id, collection_date=payload.collection_date,
        lab_name=payload.lab_name, notes=payload.notes,
    )
    soil_testing_repository.create_sample(db, sample)
    AuditLogger(db).log("SOIL_SAMPLE_CREATED", actor_id=farmer_id, actor_role="farmer", entity="soil_sample", entity_id=str(sample.id))
    db.commit()
    db.refresh(sample)
    return _to_sample_response(sample)


def list_soil_samples(db: Session, farmer_id: str, plot_id: uuid.UUID) -> SoilSampleListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    plot = plot_repository.get_owned(db, plot_id, farmer_uuid)
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)
    samples = soil_testing_repository.list_samples_for_plot(db, plot_id, farmer_uuid)
    return SoilSampleListResponse(items=[_to_sample_response(s) for s in samples], total=len(samples))


def create_soil_test_result(
    db: Session, farmer_id: str, sample_id: uuid.UUID, payload: SoilTestResultCreateRequest, settings: Settings
) -> SoilTestResultResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    sample = soil_testing_repository.get_sample_owned(db, sample_id, farmer_uuid)
    if sample is None:
        raise AppError(error_codes.NOT_FOUND, "Soil sample not found.", 404)

    result = SoilTestResult(
        farmer_id=farmer_uuid,
        soil_sample_id=sample_id,
        test_date=payload.test_date,
        ph_value=payload.ph_value,
        nitrogen_kg_per_ha=payload.nitrogen_kg_per_ha,
        phosphorus_kg_per_ha=payload.phosphorus_kg_per_ha,
        potassium_kg_per_ha=payload.potassium_kg_per_ha,
        organic_carbon_percent=payload.organic_carbon_percent,
        ec_ds_per_m=payload.ec_ds_per_m,
        micronutrients=(
            {k: str(v) for k, v in payload.micronutrients.items()} if payload.micronutrients is not None else None
        ),
    )
    soil_testing_repository.create_result(db, result)
    AuditLogger(db).log("SOIL_TEST_RESULT_CREATED", actor_id=farmer_id, actor_role="farmer", entity="soil_test_result", entity_id=str(result.id))
    db.commit()
    db.refresh(result)
    return _to_result_response(result, settings)


def list_soil_test_results(db: Session, farmer_id: str, sample_id: uuid.UUID, settings: Settings) -> SoilTestResultListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    sample = soil_testing_repository.get_sample_owned(db, sample_id, farmer_uuid)
    if sample is None:
        raise AppError(error_codes.NOT_FOUND, "Soil sample not found.", 404)
    results = soil_testing_repository.list_results_for_sample(db, sample_id, farmer_uuid)
    return SoilTestResultListResponse(items=[_to_result_response(r, settings) for r in results], total=len(results))


def upload_soil_report(
    db: Session, farmer_id: str, result_id: uuid.UUID, file_bytes: bytes, file_name: str, content_type: str,
    storage: FileStorage, settings: Settings,
) -> SoilTestResultResponse:
    """D20-10: storage of an uploaded lab-report file, mirroring
    invoice_service.upload_invoice's exact storage pattern. Deliberately
    no OCR - this project's own no-fabricated-agronomic-data convention
    means extracted values would need the same absolute confirm-gate
    invoices use, and the doc's own citation marks OCR here as optional
    ("if wanted"), not required; the structured D20-03..09 fields already
    serve as the farmer-facing summary, satisfying this row's other half."""
    farmer_uuid = uuid.UUID(farmer_id)
    result = soil_testing_repository.get_result_owned(db, result_id, farmer_uuid)
    if result is None:
        raise AppError(error_codes.NOT_FOUND, "Soil test result not found.", 404)

    storage_key = storage.save("soil-reports", file_name, io.BytesIO(file_bytes), content_type)
    result.report_storage_key = storage_key

    AuditLogger(db).log("SOIL_REPORT_UPLOADED", actor_id=farmer_id, actor_role="farmer", entity="soil_test_result", entity_id=str(result.id))
    db.commit()
    db.refresh(result)
    return _to_result_response(result, settings)


def run_soil_test_reminder_sweep(db: Session, settings: Settings) -> int:
    """D20-13/D78-10 (docs/audit/FINAL_CANONICAL_group_D.md): proactive
    reminder that a plot's most recent soil test has gone stale, run by
    the background scheduler (app/services/scheduler.py) - not
    farmer-screen-triggered, so it fires even if the farmer never opens
    Soil Testing. Mirrors input_inventory_service.run_expiry_check_sweep's
    exact shape."""
    cutoff = date.today() - timedelta(days=settings.soil_test_max_age_days)
    results = soil_testing_repository.list_stale_unalerted_soil_test_results(db, cutoff_date=cutoff)

    alerted = 0
    for result in results:
        candidate = AlertCandidate(
            category=NotificationCategory.SOIL_TEST_REMINDER,
            priority=NotificationPriority.LOW,
            message_key="SOIL_TEST_REMINDER",
            message_params={"max_age_days": settings.soil_test_max_age_days, "test_date": result.test_date.isoformat()},
            dedup_suffix=f"soil_test_reminder:{result.id}",
        )
        language_code = _language_for(db, str(result.farmer_id))
        created = notification_service.create_alert_notification(
            db, str(result.farmer_id), candidate, dedup_scope=f"soil_test_result:{result.id}", language_code=language_code,
            related_entity_type="soil_test_result", related_entity_id=str(result.id),
        )
        result.reminder_alerted_at = datetime.now(timezone.utc)
        db.commit()
        if created is not None:
            alerted += 1

    return alerted


def _language_for(db: Session, farmer_id: str) -> str:
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    if user and getattr(user, "farmer_profile", None):
        return user.farmer_profile.preferred_language_code
    return "en"


def _to_sample_response(sample: SoilSample) -> SoilSampleResponse:
    return SoilSampleResponse(
        id=sample.id, plot_id=sample.plot_id, collection_date=sample.collection_date,
        lab_name=sample.lab_name, self_tested=sample.self_tested, notes=sample.notes, created_at=sample.created_at,
    )


def _to_result_response(result: SoilTestResult, settings: Settings) -> SoilTestResultResponse:
    today = datetime.now(timezone.utc).date()
    return SoilTestResultResponse(
        id=result.id,
        soil_sample_id=result.soil_sample_id,
        test_date=result.test_date,
        ph_value=result.ph_value,
        nitrogen_kg_per_ha=result.nitrogen_kg_per_ha,
        phosphorus_kg_per_ha=result.phosphorus_kg_per_ha,
        potassium_kg_per_ha=result.potassium_kg_per_ha,
        organic_carbon_percent=result.organic_carbon_percent,
        ec_ds_per_m=result.ec_ds_per_m,
        micronutrients=result.micronutrients,
        report_storage_key=result.report_storage_key,
        is_stale=result.is_stale(today, settings.soil_test_max_age_days),
        created_at=result.created_at,
    )

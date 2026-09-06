import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ai_analysis import ResultStatus
from app.models.crop_cycle import ALLOWED_TRANSITIONS, CropCycle, CultivationStatus, FailureReason
from app.models.crop_cycle_closure_snapshot import CropCycleClosureSnapshot
from app.models.crop_cycle_stage_history import CropCycleStageHistory
from app.repositories import (
    ai_analysis_repository,
    crop_cycle_closure_snapshot_repository,
    crop_cycle_repository,
    crop_cycle_stage_history_repository,
    crop_master_repository,
    crop_variety_repository,
    harvest_repository,
    notification_repository,
    plot_repository,
)
from app.schemas.crop import (
    CropCycleCloseRequest,
    CropCycleCreateRequest,
    CropCycleListResponse,
    CropCycleResponse,
    CropCycleUpdateRequest,
    CropFailureReportRequest,
)
from app.schemas.crop_stage_history import CropCycleStageHistoryListResponse, CropCycleStageHistoryResponse
from app.services import crop_financial_service, task_service
from app.services.audit_logger import AuditLogger

_WEATHER_NOTIFICATION_CATEGORIES = {"weather_alert", "rain_alert", "heavy_rain_alert"}

_DEFAULT_PAGE_SIZE = 50

_TERMINAL_STATUSES = (CultivationStatus.CANCELLED, CultivationStatus.HARVESTED)

# D10-09/D11-01 (docs/audit/c02_lifecycle_edgecases.md): deliberately
# generic, non-prescriptive category guidance - never a specific product,
# dosage, or variety name, consistent with crop_risk_service._build_recommendation's
# own "no unvalidated agronomy advice" convention.
_RECOVERY_GUIDANCE: dict[str, str] = {
    FailureReason.DISEASE.value: "Consider requesting an expert review and a disease-resistant variety before re-sowing.",
    FailureReason.PEST.value: "Consider an expert review of pest management practices before re-sowing.",
    FailureReason.DROUGHT.value: "Consider checking irrigation availability and soil moisture before re-sowing.",
    FailureReason.FLOOD.value: "Consider inspecting drainage and soil condition before re-sowing.",
    FailureReason.WEATHER_DAMAGE.value: "Consider reviewing the weather forecast before re-sowing.",
    FailureReason.MARKET_CONDITIONS.value: "Consider checking current market prices before deciding on the next crop.",
    FailureReason.OTHER.value: "Consider reviewing what went wrong before re-sowing.",
}


def _get_owned_plot_or_404(db: Session, farmer_id: str, plot_id: uuid.UUID):
    plot = plot_repository.get_owned(db, plot_id, uuid.UUID(farmer_id))
    if plot is None:
        raise AppError(error_codes.NOT_FOUND, "Plot not found.", 404)
    return plot


def _record_stage_history(db: Session, crop_cycle_id: uuid.UUID, status: CultivationStatus) -> None:
    """Phase 2 infrastructure only - records that a transition actually
    happened, when. Never called for an unchanged status (callers check
    that before calling this), never called speculatively."""
    entry = CropCycleStageHistory(
        crop_cycle_id=crop_cycle_id,
        status=status,
        entered_at=datetime.now(timezone.utc),
    )
    crop_cycle_stage_history_repository.create(db, entry)


def create_crop_cycle(db: Session, farmer_id: str, plot_id: uuid.UUID, payload: CropCycleCreateRequest) -> CropCycleResponse:
    _get_owned_plot_or_404(db, farmer_id, plot_id)

    crop = crop_master_repository.get_active(db, payload.crop_id)
    if crop is None:
        raise AppError(error_codes.VALIDATION_ERROR, "Selected crop does not exist or is not available.", 422)

    if payload.variety_id is not None:
        # A variety_id that resolves but belongs to a DIFFERENT crop must
        # be rejected here, not just relied upon at the DB FK level -
        # the FK only guarantees the row exists somewhere, not that it's
        # the right crop's variety.
        variety = crop_variety_repository.get_for_crop(db, payload.variety_id, payload.crop_id)
        if variety is None:
            raise AppError(
                error_codes.VALIDATION_ERROR, "Selected variety does not belong to the selected crop.", 422
            )

    resown_from_id = None
    if payload.resown_from_crop_cycle_id is not None:
        previous_cycle = crop_cycle_repository.get_owned(db, payload.resown_from_crop_cycle_id, uuid.UUID(farmer_id))
        if previous_cycle is None:
            raise AppError(error_codes.NOT_FOUND, "The crop cycle being re-sown from was not found.", 404)
        if previous_cycle.plot_id != plot_id:
            raise AppError(error_codes.VALIDATION_ERROR, "resown_from_crop_cycle_id must belong to the same plot.", 422)
        if previous_cycle.cultivation_status != CultivationStatus.CANCELLED:
            raise AppError(
                error_codes.VALIDATION_ERROR, "Can only re-sow from a cancelled (failed) crop cycle.", 422
            )
        resown_from_id = previous_cycle.id

    # D6-07/D11-05 (docs/audit/FINAL_CANONICAL_group_A.md): nothing previously
    # stopped two non-terminal CropCycle rows existing on one plot at once -
    # a real offline-replay/double-tap data-integrity risk. Checked after the
    # resowing block above (not before) so a legitimate re-sow's own
    # not-cancelled validation still reports its specific 422, not this
    # generic 409 - by the time this runs, resowing's source cycle (if any)
    # is already confirmed CANCELLED and so no longer counts as active.
    if crop_cycle_repository.count_active_for_plot(db, plot_id) > 0:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            "This plot already has an active crop cycle. Close it before starting a new one.",
            409,
        )

    crop_cycle = CropCycle(
        plot_id=plot_id,
        crop_id=payload.crop_id,
        season=payload.season,
        sowing_date=payload.sowing_date,
        expected_harvest_date=payload.expected_harvest_date,
        seed_variety=payload.seed_variety,
        variety_id=payload.variety_id,
        cultivation_status=payload.initial_status,
        resown_from_crop_cycle_id=resown_from_id,
    )
    crop_cycle_repository.create(db, crop_cycle)
    db.flush()

    AuditLogger(db).log(
        "CROP_CYCLE_CREATED", actor_id=farmer_id, actor_role="farmer", entity="crop_cycle", entity_id=str(crop_cycle.id)
    )

    db.commit()
    db.refresh(crop_cycle)
    return CropCycleResponse.model_validate(crop_cycle)


def list_crop_cycles_for_plot(
    db: Session, farmer_id: str, plot_id: uuid.UUID, *, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0
) -> CropCycleListResponse:
    _get_owned_plot_or_404(db, farmer_id, plot_id)
    cycles, total = crop_cycle_repository.list_for_plot(db, plot_id, limit=limit, offset=offset)
    return CropCycleListResponse(items=[CropCycleResponse.model_validate(c) for c in cycles], total=total)


def list_my_crop_cycles(db: Session, farmer_id: str) -> CropCycleListResponse:
    """Farmer-wide crop cycle list across every farm/plot, not scoped to
    any single plot - reuses the existing list_all_for_farmer query
    (Phase 39), previously only used internally for personalization
    scoring. Needed by any farmer-wide picker (the Camera tab's "which
    crop am I checking" step) that has no plot/crop context of its own
    to scope a request to. Not paginated - matches the same unpaginated
    convention list_all_for_farmer's existing caller already relies on."""
    cycles = crop_cycle_repository.list_all_for_farmer(db, uuid.UUID(farmer_id))
    return CropCycleListResponse(items=[CropCycleResponse.model_validate(c) for c in cycles], total=len(cycles))


def get_my_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropCycleResponse:
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
    return CropCycleResponse.model_validate(crop_cycle)


def update_my_crop_cycle(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: CropCycleUpdateRequest
) -> CropCycleResponse:
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    if payload.season is not None:
        crop_cycle.season = payload.season
    if payload.seed_variety is not None:
        crop_cycle.seed_variety = payload.seed_variety

    new_sowing = payload.sowing_date if payload.sowing_date is not None else crop_cycle.sowing_date
    new_expected = (
        payload.expected_harvest_date if payload.expected_harvest_date is not None else crop_cycle.expected_harvest_date
    )
    if new_expected is not None and new_expected < new_sowing:
        raise AppError(error_codes.VALIDATION_ERROR, "expected_harvest_date cannot be before sowing_date.", 422)
    crop_cycle.sowing_date = new_sowing
    crop_cycle.expected_harvest_date = new_expected

    status_changed = False
    if payload.cultivation_status is not None and payload.cultivation_status != crop_cycle.cultivation_status:
        _validate_transition(crop_cycle.cultivation_status, payload.cultivation_status)
        crop_cycle.cultivation_status = payload.cultivation_status
        status_changed = True

    audit = AuditLogger(db)
    audit.log(
        "CROP_CYCLE_UPDATED", actor_id=farmer_id, actor_role="farmer", entity="crop_cycle", entity_id=str(crop_cycle.id)
    )
    if status_changed:
        _record_stage_history(db, crop_cycle.id, crop_cycle.cultivation_status)
        audit.log(
            "CROP_CYCLE_STATUS_CHANGED",
            actor_id=farmer_id,
            actor_role="farmer",
            entity="crop_cycle",
            entity_id=str(crop_cycle.id),
        )
        if crop_cycle.cultivation_status in _TERMINAL_STATUSES:
            task_service.cancel_all_pending_for_crop_cycle(db, farmer_id, crop_cycle.id)

    db.commit()
    db.refresh(crop_cycle)
    return CropCycleResponse.model_validate(crop_cycle)


def close_my_crop_cycle(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: CropCycleCloseRequest
) -> CropCycleResponse:
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    _validate_transition(crop_cycle.cultivation_status, CultivationStatus.HARVESTED)

    if payload.actual_harvest_date < crop_cycle.sowing_date:
        raise AppError(error_codes.VALIDATION_ERROR, "actual_harvest_date cannot be before sowing_date.", 422)

    crop_cycle.actual_harvest_date = payload.actual_harvest_date
    crop_cycle.cultivation_status = CultivationStatus.HARVESTED
    crop_cycle.lessons_learned = payload.lessons_learned

    audit = AuditLogger(db)
    audit.log(
        "CROP_CYCLE_CLOSED", actor_id=farmer_id, actor_role="farmer", entity="crop_cycle", entity_id=str(crop_cycle.id)
    )
    _record_stage_history(db, crop_cycle.id, crop_cycle.cultivation_status)
    audit.log(
        "CROP_CYCLE_STATUS_CHANGED",
        actor_id=farmer_id,
        actor_role="farmer",
        entity="crop_cycle",
        entity_id=str(crop_cycle.id),
    )
    task_service.cancel_all_pending_for_crop_cycle(db, farmer_id, crop_cycle.id)
    _create_closure_snapshot(db, farmer_id, crop_cycle)

    db.commit()
    db.refresh(crop_cycle)
    return CropCycleResponse.model_validate(crop_cycle)


def _create_closure_snapshot(db: Session, farmer_id: str, crop_cycle: CropCycle) -> None:
    """D97-02..09 (docs/audit/FINAL_CANONICAL_group_D.md): freezes the
    cycle's outcome at the exact moment of closure - every other view of
    this data is a live aggregate that could drift after closure if
    underlying rows are later edited. Consolidates what the source audit
    doc separately proposed as CropCycle columns (D97-02/03) and a shared
    table (D97-04..09) into one table - see the model's own docstring."""
    harvest = harvest_repository.get_most_recent_harvest_by_crop_cycle(db, crop_cycle.id)

    financials = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle.id)

    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle.id, uuid.UUID(farmer_id))
    disease_detected = [a for a in analyses if a.result_status == ResultStatus.DISEASE_DETECTED]
    disease_summary = {
        "total_photos_analyzed": len(analyses),
        "disease_detected_count": len(disease_detected),
        "diseases_observed": sorted({a.predicted_class for a in disease_detected if a.predicted_class}),
    }

    weather_notifications = [
        n for n in notification_repository.list_for_related_entity(db, "crop_cycle", str(crop_cycle.id))
        if n.category.value in _WEATHER_NOTIFICATION_CATEGORIES
    ]
    weather_impact_summary = {
        "weather_alert_count": len(weather_notifications),
        "categories": sorted({n.category.value for n in weather_notifications}),
    }

    snapshot = CropCycleClosureSnapshot(
        crop_cycle_id=crop_cycle.id,
        harvest_quantity=harvest.actual_quantity if harvest and harvest.actual_quantity is not None else (harvest.estimated_quantity if harvest else None),
        harvest_quantity_unit=harvest.unit if harvest else None,
        quality_grade=harvest.quality_grade if harvest else None,
        harvest_status=harvest.status.value if harvest else None,
        actual_cost=financials.actual_cost,
        actual_revenue=financials.actual_revenue,
        actual_profit_loss=financials.actual_profit_loss,
        disease_summary=disease_summary,
        weather_impact_summary=weather_impact_summary,
    )
    crop_cycle_closure_snapshot_repository.create(db, snapshot)


def report_crop_failure(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: CropFailureReportRequest
) -> CropCycleResponse:
    """D10-01/D10-02/D10-03 (docs/audit/c02_lifecycle_edgecases.md): a
    distinct "report failure" workflow, not the generic status-only
    cancel `update_my_crop_cycle` already supports - captures WHY, so a
    reported failure stays distinguishable from a farmer simply changing
    their mind. Internally still a CANCELLED transition (no new terminal
    state was invented), so every existing rule about CANCELLED being
    terminal/non-reversible still applies unchanged."""
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    _validate_transition(crop_cycle.cultivation_status, CultivationStatus.CANCELLED)

    # D10-07 (docs/audit/FINAL_CANONICAL_group_A.md): OTHER is a catch-all
    # with no reason text of its own - a note is the only way it carries
    # any real information, so it's required specifically for this one
    # value, unlike every other reason where the enum value is self-
    # explanatory and a note is a genuinely optional extra.
    if payload.failure_reason == FailureReason.OTHER and not (payload.failure_reason_note or "").strip():
        raise AppError(error_codes.VALIDATION_ERROR, "failure_reason_note is required when failure_reason is 'other'.", 422)

    crop_cycle.cultivation_status = CultivationStatus.CANCELLED
    crop_cycle.failure_reason = payload.failure_reason.value
    crop_cycle.failure_reason_note = payload.failure_reason_note

    audit = AuditLogger(db)
    audit.log(
        "CROP_CYCLE_FAILURE_REPORTED", actor_id=farmer_id, actor_role="farmer", entity="crop_cycle", entity_id=str(crop_cycle.id)
    )
    _record_stage_history(db, crop_cycle.id, crop_cycle.cultivation_status)
    audit.log(
        "CROP_CYCLE_STATUS_CHANGED", actor_id=farmer_id, actor_role="farmer", entity="crop_cycle", entity_id=str(crop_cycle.id)
    )
    task_service.cancel_all_pending_for_crop_cycle(db, farmer_id, crop_cycle.id)

    db.commit()
    db.refresh(crop_cycle)

    response = CropCycleResponse.model_validate(crop_cycle)
    response.recommended_next_action = _RECOVERY_GUIDANCE.get(payload.failure_reason.value)
    return response


def _validate_transition(current: CultivationStatus, target: CultivationStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            f"Cannot change status from '{current.value}' to '{target.value}'.",
            409,
        )


def get_stage_history_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropCycleStageHistoryListResponse:
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    items = crop_cycle_stage_history_repository.list_for_crop_cycle(db, crop_cycle_id)
    return CropCycleStageHistoryListResponse(
        items=[CropCycleStageHistoryResponse.model_validate(i) for i in items], total=len(items)
    )

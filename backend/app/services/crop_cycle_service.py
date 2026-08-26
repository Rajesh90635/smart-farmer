import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.crop_cycle import ALLOWED_TRANSITIONS, CropCycle, CultivationStatus
from app.models.crop_cycle_stage_history import CropCycleStageHistory
from app.repositories import crop_cycle_repository, crop_cycle_stage_history_repository, crop_master_repository, crop_variety_repository, plot_repository
from app.schemas.crop import (
    CropCycleCloseRequest,
    CropCycleCreateRequest,
    CropCycleListResponse,
    CropCycleResponse,
    CropCycleUpdateRequest,
)
from app.schemas.crop_stage_history import CropCycleStageHistoryListResponse, CropCycleStageHistoryResponse
from app.services.audit_logger import AuditLogger

_DEFAULT_PAGE_SIZE = 50


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

    crop_cycle = CropCycle(
        plot_id=plot_id,
        crop_id=payload.crop_id,
        season=payload.season,
        sowing_date=payload.sowing_date,
        expected_harvest_date=payload.expected_harvest_date,
        seed_variety=payload.seed_variety,
        variety_id=payload.variety_id,
        cultivation_status=CultivationStatus.PLANNED,
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

    db.commit()
    db.refresh(crop_cycle)
    return CropCycleResponse.model_validate(crop_cycle)


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

"""
Crop endpoints: crop master search (for the searchable crop-selection UI)
plus crop-cycle CRUD. Paths mix /crops/master, /plots/{plot_id}/crops, and
/crops/{crop_cycle_id} - no single router prefix, same reasoning as plots.py.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.repositories import crop_master_repository
from app.schemas.crop import (
    CropCycleCloseRequest,
    CropCycleCreateRequest,
    CropCycleListResponse,
    CropCycleResponse,
    CropCycleUpdateRequest,
    CropFailureReportRequest,
    CropMasterResponse,
    CropYearSummaryResponse,
)
from app.schemas.crop_grade_option import CropGradeOptionCreateRequest, CropGradeOptionResponse
from app.schemas.crop_stage_history import CropCycleStageHistoryListResponse
from app.services import crop_cycle_service, crop_grade_option_service

router = APIRouter(tags=["crops"])


@router.get("/crops/master", response_model=list[CropMasterResponse])
def search_crop_master(
    query: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> list[CropMasterResponse]:
    results = crop_master_repository.search(db, query, limit=limit)
    return [CropMasterResponse.model_validate(c) for c in results]


@router.get("/crops/master/{crop_id}/grade-options", response_model=list[CropGradeOptionResponse])
def list_crop_grade_options(
    crop_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> list[CropGradeOptionResponse]:
    """D52-02: empty until an admin has configured real grade options for
    this crop - farmers see the configured choices, if any, before
    entering a listing's quality_grade."""
    return crop_grade_option_service.list_grade_options(db, crop_id)


@router.post("/crops/master/{crop_id}/grade-options", response_model=CropGradeOptionResponse, status_code=status.HTTP_201_CREATED)
def add_crop_grade_option(
    crop_id: uuid.UUID,
    payload: CropGradeOptionCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> CropGradeOptionResponse:
    return crop_grade_option_service.add_grade_option(db, crop_id, payload)


@router.post("/plots/{plot_id}/crops", response_model=CropCycleResponse, status_code=status.HTTP_201_CREATED)
def create_crop_cycle(
    plot_id: uuid.UUID,
    payload: CropCycleCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleResponse:
    return crop_cycle_service.create_crop_cycle(db, current_user.user_id, plot_id, payload)


@router.get("/plots/{plot_id}/crops", response_model=CropCycleListResponse)
def list_crop_cycles(
    plot_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleListResponse:
    return crop_cycle_service.list_crop_cycles_for_plot(db, current_user.user_id, plot_id, limit=limit, offset=offset)


@router.get("/crops", response_model=CropCycleListResponse)
def list_my_crop_cycles(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleListResponse:
    """Farmer-wide, across every farm/plot - for pickers that have no
    plot/crop context of their own (e.g. the Camera tab's "which crop am
    I checking" step)."""
    return crop_cycle_service.list_my_crop_cycles(db, current_user.user_id)


@router.get("/crops/{crop_cycle_id}", response_model=CropCycleResponse)
def get_crop_cycle(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleResponse:
    return crop_cycle_service.get_my_crop_cycle(db, current_user.user_id, crop_cycle_id)


@router.put("/crops/{crop_cycle_id}", response_model=CropCycleResponse)
def update_crop_cycle(
    crop_cycle_id: uuid.UUID,
    payload: CropCycleUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleResponse:
    return crop_cycle_service.update_my_crop_cycle(db, current_user.user_id, crop_cycle_id, payload)


@router.post("/crops/{crop_cycle_id}/close", response_model=CropCycleResponse)
def close_crop_cycle(
    crop_cycle_id: uuid.UUID,
    payload: CropCycleCloseRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleResponse:
    return crop_cycle_service.close_my_crop_cycle(db, current_user.user_id, crop_cycle_id, payload)


@router.post("/crops/{crop_cycle_id}/report-failure", response_model=CropCycleResponse)
def report_crop_failure(
    crop_cycle_id: uuid.UUID,
    payload: CropFailureReportRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleResponse:
    """Distinct from the generic `PUT /crops/{id}` status-only cancel -
    captures WHY the crop failed (D10-01/D10-02/D10-03) and returns
    category-driven, non-prescriptive recovery guidance (D10-09/D11-01)."""
    return crop_cycle_service.report_crop_failure(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crops/{crop_cycle_id}/stage-history", response_model=CropCycleStageHistoryListResponse)
def get_crop_cycle_stage_history(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCycleStageHistoryListResponse:
    """Read-only. Phase 2 infrastructure - no plan-generation here, just
    the actual recorded transition history for this crop cycle."""
    return crop_cycle_service.get_stage_history_for_crop_cycle(db, current_user.user_id, crop_cycle_id)


@router.get("/crops/{crop_cycle_id}/year-summary", response_model=CropYearSummaryResponse)
def get_crop_year_summary(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropYearSummaryResponse:
    """D13-06 (docs/audit/FINAL_CANONICAL_group_A.md): calendar-year rollup
    of this cycle's own harvests/stage changes - read-only aggregation."""
    return crop_cycle_service.get_crop_year_summary(db, current_user.user_id, crop_cycle_id)

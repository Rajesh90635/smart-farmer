"""
Plot endpoints. Paths are intentionally mixed (/farms/{farm_id}/plots for
create/list, /plots/{plot_id} for single-resource operations) to match the
approved API examples, so this router has no single prefix - every route
declares its full path.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.plot import PlotCreateRequest, PlotListResponse, PlotResponse, PlotUpdateRequest
from app.schemas.plot_history import PlotSoilHistoryListResponse, PlotWaterHistoryListResponse
from app.services import plot_service

router = APIRouter(tags=["plots"])


@router.post("/farms/{farm_id}/plots", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
def create_plot(
    farm_id: uuid.UUID,
    payload: PlotCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotResponse:
    return plot_service.create_plot(db, current_user.user_id, farm_id, payload)


@router.get("/farms/{farm_id}/plots", response_model=PlotListResponse)
def list_plots_for_farm(
    farm_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotListResponse:
    return plot_service.list_plots_for_farm(db, current_user.user_id, farm_id, limit=limit, offset=offset)


@router.get("/plots/{plot_id}", response_model=PlotResponse)
def get_plot(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotResponse:
    return plot_service.get_my_plot(db, current_user.user_id, plot_id)


@router.put("/plots/{plot_id}", response_model=PlotResponse)
def update_plot(
    plot_id: uuid.UUID,
    payload: PlotUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotResponse:
    return plot_service.update_my_plot(db, current_user.user_id, plot_id, payload)


@router.get("/plots/{plot_id}/soil-history", response_model=PlotSoilHistoryListResponse)
def get_plot_soil_history(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotSoilHistoryListResponse:
    """D19-04 (docs/audit/FINAL_CANONICAL_group_A.md). Read-only - the
    actual recorded soil_type/soil_category changes for this plot."""
    return plot_service.get_soil_history_for_plot(db, current_user.user_id, plot_id)


@router.get("/plots/{plot_id}/water-history", response_model=PlotWaterHistoryListResponse)
def get_plot_water_history(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotWaterHistoryListResponse:
    """D17-06 (docs/audit/FINAL_CANONICAL_group_A.md). Read-only - the
    actual recorded water_availability changes for this plot."""
    return plot_service.get_water_history_for_plot(db, current_user.user_id, plot_id)


@router.delete("/plots/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_plot(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    plot_service.deactivate_my_plot(db, current_user.user_id, plot_id)

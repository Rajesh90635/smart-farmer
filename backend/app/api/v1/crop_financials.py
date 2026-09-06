"""
Phase 31 endpoints: farmer-entered cost estimates + the estimated-vs-
actual financial summary.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.models.crop_cycle import Season
from app.schemas.cost_estimate import (
    CropCostEstimateCreateRequest,
    CropCostEstimateListResponse,
    CropCostEstimateResponse,
    CropFinancialSummaryResponse,
    FarmFinancialSummaryResponse,
    PlotFinancialSummaryResponse,
    PlotFinancialTotalsResponse,
    SeasonFinancialSummaryResponse,
    SeasonFinancialTotalsResponse,
)
from app.schemas.profit_forecast import CropProfitForecastResponse
from app.services import crop_financial_service, profit_forecast_service

router = APIRouter(tags=["crop-financials"])


@router.post("/crop-cycles/{crop_cycle_id}/cost-estimates", response_model=CropCostEstimateResponse, status_code=201)
def create_cost_estimate(
    crop_cycle_id: uuid.UUID,
    payload: CropCostEstimateCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCostEstimateResponse:
    return crop_financial_service.create_estimate(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/cost-estimates", response_model=CropCostEstimateListResponse)
def list_cost_estimates(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropCostEstimateListResponse:
    return crop_financial_service.list_estimates(db, current_user.user_id, crop_cycle_id)


@router.delete("/cost-estimates/{estimate_id}", status_code=204)
def delete_cost_estimate(
    estimate_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    crop_financial_service.delete_estimate(db, current_user.user_id, estimate_id)


@router.get("/crop-cycles/{crop_cycle_id}/financial-summary", response_model=CropFinancialSummaryResponse)
def get_financial_summary(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropFinancialSummaryResponse:
    return crop_financial_service.get_financial_summary(db, current_user.user_id, crop_cycle_id)


@router.get("/crop-cycles/{crop_cycle_id}/profit-forecast", response_model=CropProfitForecastResponse)
def get_profit_forecast(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropProfitForecastResponse:
    return profit_forecast_service.get_profit_forecast(db, current_user.user_id, crop_cycle_id)


@router.get("/plots/{plot_id}/financial-summary", response_model=PlotFinancialTotalsResponse)
def get_plot_financial_summary(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotFinancialTotalsResponse:
    """D70-04 (docs/audit/FINAL_CANONICAL_group_C.md)."""
    return crop_financial_service.get_plot_financial_summary(db, current_user.user_id, plot_id)


@router.get("/farmers/me/seasons/{season}/financial-summary", response_model=SeasonFinancialTotalsResponse)
def get_season_financial_summary(
    season: Season,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SeasonFinancialTotalsResponse:
    """D70-05 (docs/audit/FINAL_CANONICAL_group_C.md)."""
    return crop_financial_service.get_season_financial_summary(db, current_user.user_id, season)


@router.get("/plots/{plot_id}/pnl-summary", response_model=PlotFinancialSummaryResponse)
def get_plot_pnl(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PlotFinancialSummaryResponse:
    """D71-05 (docs/audit/FINAL_CANONICAL_group_C.md)."""
    return crop_financial_service.get_plot_pnl(db, current_user.user_id, plot_id)


@router.get("/farms/{farm_id}/pnl-summary", response_model=FarmFinancialSummaryResponse)
def get_farm_pnl(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmFinancialSummaryResponse:
    """D71-06 (docs/audit/FINAL_CANONICAL_group_C.md)."""
    return crop_financial_service.get_farm_pnl(db, current_user.user_id, farm_id)


@router.get("/farmers/me/seasons/{season}/pnl-summary", response_model=SeasonFinancialSummaryResponse)
def get_season_pnl(
    season: Season,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SeasonFinancialSummaryResponse:
    """D71-07 (docs/audit/FINAL_CANONICAL_group_C.md)."""
    return crop_financial_service.get_season_pnl(db, current_user.user_id, season)

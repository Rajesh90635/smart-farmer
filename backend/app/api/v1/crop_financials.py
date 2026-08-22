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
from app.schemas.cost_estimate import CropCostEstimateCreateRequest, CropCostEstimateListResponse, CropCostEstimateResponse, CropFinancialSummaryResponse
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

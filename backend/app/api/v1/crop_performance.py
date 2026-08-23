"""
Phase 38 endpoints: crop performance score and crop-to-crop comparison.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import get_db
from app.schemas.crop_comparison import CropComparisonResponse
from app.schemas.crop_performance import PerformanceScoreResponse
from app.schemas.input_roi import InputRoiResponse
from app.schemas.irrigation_intelligence import IrrigationIntelligenceResponse
from app.services import crop_comparison_service, crop_performance_service, input_roi_service, irrigation_intelligence_service
from app.services.weather.weather_provider import WeatherProvider

router = APIRouter(tags=["crop-performance"])


@router.get("/crop-cycles/{crop_cycle_id}/performance", response_model=PerformanceScoreResponse)
def get_performance_score(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PerformanceScoreResponse:
    return crop_performance_service.get_performance_score(db, current_user.user_id, crop_cycle_id)


@router.get("/crop-cycles/{crop_cycle_id}/comparison/{other_crop_cycle_id}", response_model=CropComparisonResponse)
def compare_crop_cycles(
    crop_cycle_id: uuid.UUID,
    other_crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropComparisonResponse:
    return crop_comparison_service.compare_crop_cycles(db, current_user.user_id, crop_cycle_id, other_crop_cycle_id)


@router.get("/crop-cycles/{crop_cycle_id}/input-roi", response_model=InputRoiResponse)
def get_input_roi(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputRoiResponse:
    return input_roi_service.get_input_roi(db, current_user.user_id, crop_cycle_id)


@router.get("/crop-cycles/{crop_cycle_id}/irrigation-intelligence", response_model=IrrigationIntelligenceResponse)
def get_irrigation_intelligence(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    weather_provider: WeatherProvider = Depends(get_weather_provider),
    settings: Settings = Depends(get_settings),
) -> IrrigationIntelligenceResponse:
    return irrigation_intelligence_service.get_irrigation_intelligence(db, current_user.user_id, crop_cycle_id, weather_provider, settings)

"""
Phase 33 endpoint: crop risk score.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import get_db
from app.schemas.crop_risk import CropRiskScoreResponse
from app.services import crop_risk_service
from app.services.weather.weather_provider import WeatherProvider

router = APIRouter(tags=["crop-risk"])


@router.get("/crop-cycles/{crop_cycle_id}/risk-score", response_model=CropRiskScoreResponse)
def get_risk_score(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    weather_provider: WeatherProvider = Depends(get_weather_provider),
    settings: Settings = Depends(get_settings),
) -> CropRiskScoreResponse:
    return crop_risk_service.get_risk_score(db, current_user.user_id, crop_cycle_id, weather_provider=weather_provider, settings=settings)

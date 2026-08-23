"""
Phase 37 endpoint: crop-cycle-scoped weather action advisor.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import get_db
from app.schemas.weather_action import CropWeatherActionResponse
from app.services import weather_action_engine_service
from app.services.weather.weather_provider import WeatherProvider

router = APIRouter(tags=["weather-actions"])


@router.get("/crop-cycles/{crop_cycle_id}/weather-actions", response_model=CropWeatherActionResponse)
def get_weather_actions(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    weather_provider: WeatherProvider = Depends(get_weather_provider),
    settings: Settings = Depends(get_settings),
) -> CropWeatherActionResponse:
    return weather_action_engine_service.get_weather_actions(db, current_user.user_id, crop_cycle_id, weather_provider, settings)

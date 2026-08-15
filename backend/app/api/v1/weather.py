"""
Weather endpoints. Flutter never calls the weather provider directly -
only this route, through WeatherService, does - protecting API keys and
allowing the provider to be swapped (see docs/WEATHER_ARCHITECTURE.md).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import get_db
from app.repositories import farm_repository, user_repository
from app.schemas.weather import FarmWeatherResponse
from app.services import weather_alert_orchestration_service, weather_service
from app.services.weather.weather_provider import WeatherProvider

router = APIRouter(tags=["weather"])


@router.get("/farms/{farm_id}/weather", response_model=FarmWeatherResponse)
def get_farm_weather(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    provider: WeatherProvider = Depends(get_weather_provider),
    settings: Settings = Depends(get_settings),
) -> FarmWeatherResponse:
    weather = weather_service.get_farm_weather(db, current_user.user_id, farm_id, provider, settings)

    # Alert generation is best-effort - a failure here must never break
    # the weather response the farmer is waiting on.
    try:
        farm = farm_repository.get_owned(db, farm_id, uuid.UUID(current_user.user_id))
        farmer_user = user_repository.get_by_id(db, uuid.UUID(current_user.user_id))
        language_code = farmer_user.farmer_profile.preferred_language_code if farmer_user and farmer_user.farmer_profile else "en"
        if farm is not None:
            weather_alert_orchestration_service.generate_alerts_for_farm_weather(
                db, current_user.user_id, farm, weather, language_code, settings
            )
    except Exception:  # noqa: BLE001 - alert generation must degrade silently, never break the weather endpoint
        db.rollback()

    return weather

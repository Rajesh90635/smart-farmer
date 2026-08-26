"""
Smart Farmer Assistant endpoints. Voice input/output is handled entirely
client-side via device-native STT/TTS (the same architecture decision
Prompt 7 made for TTS) - this backend only ever sees and returns text,
consistent with the free-first, no-paid-speech-API requirement. See
docs/VOICE_ASSISTANT.md.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.ai_model_dependency import get_model_provider
from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import get_db
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    DailySummaryResponse,
    FeedbackCreateRequest,
    PreferenceResponse,
    PreferenceUpdateRequest,
)
from app.services import assistant_extras_service, assistant_service
from app.services.ai.model_provider import ModelProvider
from app.services.weather.weather_provider import WeatherProvider

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    weather_provider: WeatherProvider = Depends(get_weather_provider),
    model_provider: ModelProvider = Depends(get_model_provider),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    return assistant_service.send_message(db, current_user.user_id, payload, weather_provider, model_provider, settings)


@router.get("/history", response_model=ConversationHistoryResponse)
def get_active_history(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> ConversationHistoryResponse:
    return assistant_service.get_active_history(db, current_user.user_id)


@router.get("/history/{conversation_id}", response_model=ConversationHistoryResponse)
def get_history(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> ConversationHistoryResponse:
    return assistant_service.get_history(db, current_user.user_id, conversation_id)


@router.delete("/history/{conversation_id}", status_code=204)
def delete_history(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    assistant_service.delete_history(db, current_user.user_id, conversation_id)


@router.post("/feedback/{message_id}", status_code=204)
def submit_feedback(
    message_id: uuid.UUID,
    payload: FeedbackCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    assistant_extras_service.submit_feedback(db, current_user.user_id, message_id, payload)


@router.get("/preferences", response_model=PreferenceResponse)
def get_preferences(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    return assistant_extras_service.get_or_create_preferences(db, current_user.user_id)


@router.put("/preferences", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    return assistant_extras_service.update_preferences(db, current_user.user_id, payload)


@router.get("/daily-summary", response_model=DailySummaryResponse)
def daily_summary(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    weather_provider: WeatherProvider = Depends(get_weather_provider),
    settings: Settings = Depends(get_settings),
) -> DailySummaryResponse:
    return assistant_extras_service.get_daily_summary(db, current_user.user_id, weather_provider, settings)

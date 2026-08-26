"""
Assistant orchestrator:

Flutter -> Assistant API -> Authentication (existing JWT, unchanged)
        -> Safety pre-check (prescription requests never reach routing)
        -> Intent Router (deterministic)
        -> Authorized Tools (farmer-scoped)
        -> Response Generator (templated)
        -> Safety post-check (defense in depth)
        -> Persistence (AssistantMessage - intent/tools/sources always recorded)
        -> Flutter

Every farmer message and every assistant response is persisted with full
provenance (intent, tools_called, sources) - this is what makes the AI
audit trail a real database fact, not a log line someone forgot to write.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.farmer_messages import get_message
from app.models.assistant_conversation import AssistantMessage, MessageRole
from app.repositories import assistant_repository, user_repository
from app.schemas.assistant import ChatRequest, ChatResponse, ConversationHistoryResponse, MessageResponse
from app.services.ai.model_provider import ModelProvider
from app.services.assistant import tools
from app.services.assistant.intent_router import Intent, detect_intent
from app.services.assistant.response_generator import generate_response
from app.services.assistant.safety_validator import contains_unsafe_prescription_language, is_prescription_request
from app.services.audit_logger import AuditLogger
from app.services.weather.weather_provider import WeatherProvider


def _resolve_language(db: Session, farmer_id: str, requested: str | None) -> str:
    if requested:
        return requested
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    if user and getattr(user, "farmer_profile", None):
        return user.farmer_profile.preferred_language_code
    return "en"


def _call_tool_for_intent(db: Session, farmer_id: str, intent: Intent, weather_provider: WeatherProvider, settings: Settings) -> tuple[dict, list[str]]:
    if intent == Intent.CROP_STATUS:
        return tools.get_crop_status(db, farmer_id), ["get_crop_status"]
    if intent == Intent.DISEASE_STATUS:
        return tools.get_disease_status(db, farmer_id, settings), ["get_disease_status"]
    if intent == Intent.WEATHER:
        return tools.get_weather_status(db, farmer_id, weather_provider, settings), ["get_weather_status"]
    if intent in (Intent.HARVEST_READINESS, Intent.HARVEST_STATUS, Intent.SELL_CROP):
        return tools.get_harvest_status(db, farmer_id), ["get_harvest_status"]
    if intent == Intent.BUYER_OFFER:
        return tools.get_buyer_offers(db, farmer_id), ["get_buyer_offers"]
    if intent == Intent.MY_SALES:
        return tools.get_my_sales(db, farmer_id), ["get_my_sales"]
    if intent == Intent.MY_ORDERS:
        return tools.get_my_orders(db, farmer_id), ["get_my_orders"]
    if intent == Intent.DELIVERY_STATUS:
        return tools.get_delivery_status(db, farmer_id), ["get_delivery_status"]
    if intent == Intent.EXPERT_CASE:
        return tools.get_expert_case_status(db, farmer_id), ["get_expert_case_status"]
    if intent in (Intent.FIND_SEED, Intent.PRICE_CHECK):
        return tools.get_seed_products(db), ["get_seed_products"]
    return {}, []


def send_message(
    db: Session, farmer_id: str, payload: ChatRequest, weather_provider: WeatherProvider, model_provider: ModelProvider, settings: Settings
) -> ChatResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    language_code = _resolve_language(db, farmer_id, payload.language_code)

    if payload.conversation_id:
        conversation = assistant_repository.get_conversation_owned(db, payload.conversation_id, farmer_uuid)
        if conversation is None:
            raise AppError(error_codes.NOT_FOUND, "Conversation not found.", 404)
    else:
        conversation = assistant_repository.get_or_create_active_conversation(db, farmer_uuid)

    farmer_message = AssistantMessage(conversation_id=conversation.id, role=MessageRole.FARMER, content=payload.message, language_code=language_code)
    assistant_repository.create_message(db, farmer_message)
    db.flush()

    if is_prescription_request(payload.message):
        response_text = get_message("assistant_prescription_redirect", language_code)
        intent_value = "prescription_blocked"
        tools_called: list[str] = []
        sources: list[str] = []
        confidence = None
    else:
        intent = detect_intent(payload.message)
        tool_result, tools_called = _call_tool_for_intent(db, farmer_id, intent, weather_provider, settings)
        response_text, confidence, sources = generate_response(intent, tool_result, language_code)
        intent_value = intent.value

        if contains_unsafe_prescription_language(response_text):
            response_text = get_message("assistant_prescription_redirect", language_code)
            confidence = None
            sources = []

    assistant_message = AssistantMessage(
        conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=response_text, language_code=language_code,
        intent=intent_value, tools_called=tools_called, sources=sources, confidence=confidence,
    )
    assistant_repository.create_message(db, assistant_message)

    AuditLogger(db).log("ASSISTANT_MESSAGE_SENT", actor_id=farmer_id, actor_role="farmer", entity="assistant_conversation", entity_id=str(conversation.id))

    db.commit()
    db.refresh(farmer_message)
    db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation.id,
        farmer_message=MessageResponse.model_validate(farmer_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )


def get_active_history(db: Session, farmer_id: str) -> ConversationHistoryResponse:
    """For a chat screen opening cold, with no conversation_id in hand
    yet - returns the farmer's current active conversation, or an empty
    result if they've never sent a message (never creates one just from
    viewing)."""
    conversation = assistant_repository.get_active_conversation(db, uuid.UUID(farmer_id))
    if conversation is None:
        return ConversationHistoryResponse(conversation_id=None, messages=[])
    return ConversationHistoryResponse(conversation_id=conversation.id, messages=[MessageResponse.model_validate(m) for m in conversation.messages])


def get_history(db: Session, farmer_id: str, conversation_id: uuid.UUID) -> ConversationHistoryResponse:
    conversation = assistant_repository.get_conversation_owned(db, conversation_id, uuid.UUID(farmer_id))
    if conversation is None:
        raise AppError(error_codes.NOT_FOUND, "Conversation not found.", 404)
    return ConversationHistoryResponse(conversation_id=conversation.id, messages=[MessageResponse.model_validate(m) for m in conversation.messages])


def delete_history(db: Session, farmer_id: str, conversation_id: uuid.UUID) -> None:
    conversation = assistant_repository.get_conversation_owned(db, conversation_id, uuid.UUID(farmer_id))
    if conversation is None:
        raise AppError(error_codes.NOT_FOUND, "Conversation not found.", 404)
    conversation.is_archived = True
    AuditLogger(db).log("ASSISTANT_HISTORY_DELETED", actor_id=farmer_id, actor_role="farmer", entity="assistant_conversation", entity_id=str(conversation.id))
    db.commit()

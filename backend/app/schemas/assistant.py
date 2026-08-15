import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assistant_conversation import ConfidenceLevel, MessageRole
from app.models.assistant_feedback import FeedbackType, ResponseMode


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    language_code: str | None = None  # defaults to the farmer's own preferred_language_code if omitted
    conversation_id: uuid.UUID | None = None  # continues an existing conversation, or starts/reuses the active one


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    language_code: str
    intent: str | None
    tools_called: list[str] | None
    sources: list[str] | None
    confidence: ConfidenceLevel | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    farmer_message: MessageResponse
    assistant_message: MessageResponse


class ConversationHistoryResponse(BaseModel):
    conversation_id: uuid.UUID
    messages: list[MessageResponse]


class FeedbackCreateRequest(BaseModel):
    feedback_type: FeedbackType
    note: str | None = Field(default=None, max_length=500)


class PreferenceResponse(BaseModel):
    response_mode: ResponseMode
    voice_enabled: bool
    daily_summary_enabled: bool
    proactive_suggestions_enabled: bool

    model_config = {"from_attributes": True}


class PreferenceUpdateRequest(BaseModel):
    response_mode: ResponseMode | None = None
    voice_enabled: bool | None = None
    daily_summary_enabled: bool | None = None
    proactive_suggestions_enabled: bool | None = None


class DailySummaryResponse(BaseModel):
    language_code: str
    lines: list[str]
    generated_at: datetime

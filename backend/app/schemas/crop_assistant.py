import uuid

from pydantic import BaseModel, Field


class CropAssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class CropAssistantResponse(BaseModel):
    """Deliberately stateless (Phase 36) - no conversation is persisted.
    The existing farmer-wide assistant (Prompt 11) already has full
    conversation history via AssistantConversation/AssistantMessage; this
    narrower, crop-scoped variant does not need its own persistent
    history to satisfy this phase's requirement, and adding one would be
    unjustified scope. context_used names exactly which real sources
    backed the answer - never a black box. limitations states in plain
    language what was NOT available, when relevant."""
    crop_cycle_id: uuid.UUID
    intent: str
    answer: str
    context_used: list[str]
    limitations: list[str]

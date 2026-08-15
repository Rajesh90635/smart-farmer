import uuid

from pydantic import BaseModel

from app.models.ai_analysis import ResultStatus


class FarmerFriendlyAnalysisResponse(BaseModel):
    analysis_id: uuid.UUID
    language_code: str
    result_status: ResultStatus
    title: str
    what_we_noticed: str | None = None
    confidence_wording: str | None = None
    next_action: str | None = None
    audio_text: str

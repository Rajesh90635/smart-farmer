from datetime import datetime

from pydantic import BaseModel, Field

from app.models.consent_record import ConsentStatus, ConsentType


class ConsentRecordResponse(BaseModel):
    consent_type: ConsentType
    version: str
    status: ConsentStatus
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ConsentUpsertRequest(BaseModel):
    consent_type: ConsentType
    version: str = Field(min_length=1, max_length=20)
    status: ConsentStatus = ConsentStatus.ACCEPTED

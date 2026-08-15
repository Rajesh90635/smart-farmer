import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.localization import is_supported_language
from app.models.user import AccountStatus


class FarmerProfileResponse(BaseModel):
    user_id: uuid.UUID
    phone_number: str
    full_name: str
    preferred_language_code: str
    preferred_voice_language_code: str
    status: AccountStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmerProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    preferred_language_code: str | None = None
    preferred_voice_language_code: str | None = None

    @field_validator("preferred_language_code")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        if v is not None and not is_supported_language(v):
            raise ValueError(f"Unsupported language code: {v}")
        return v

    @field_validator("preferred_voice_language_code")
    @classmethod
    def validate_voice_language(cls, v: str | None) -> str | None:
        if v is not None and not is_supported_language(v):
            raise ValueError(f"Unsupported voice language code: {v}")
        return v

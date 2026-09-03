from pydantic import BaseModel, Field, field_validator

from app.core.localization import is_supported_language
from app.core.phone_utils import normalize_phone_number
from app.core.security_passwords import is_strong_password
from app.models.consent_record import ConsentType


class ConsentInput(BaseModel):
    consent_type: ConsentType
    version: str = Field(min_length=1, max_length=20)


class RegisterRequest(BaseModel):
    phone_number: str
    password: str
    full_name: str = Field(min_length=2, max_length=200)
    preferred_language_code: str = "en"
    preferred_voice_language_code: str | None = None
    consents: list[ConsentInput]

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # Canonicalizes to +91XXXXXXXXXX (see app/core/phone_utils.py) -
        # this is what makes the DATABASE always store the canonical
        # form for a newly registered user, regardless of which of the
        # three accepted input formats the farmer typed. ValueError here
        # becomes a normal 422, same as the old regex-only check did for
        # genuinely invalid input.
        try:
            return normalize_phone_number(v)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not is_strong_password(v):
            raise ValueError("password must be at least 8 characters and contain a letter and a digit")
        return v

    @field_validator("preferred_language_code")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if not is_supported_language(v):
            raise ValueError(f"Unsupported language code: {v}")
        return v

    @field_validator("preferred_voice_language_code")
    @classmethod
    def validate_voice_language(cls, v: str | None) -> str | None:
        if v is not None and not is_supported_language(v):
            raise ValueError(f"Unsupported voice language code: {v}")
        return v


class LoginRequest(BaseModel):
    phone_number: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not is_strong_password(v):
            raise ValueError("password must be at least 8 characters and contain a letter and a digit")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

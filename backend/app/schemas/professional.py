import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.localization import is_supported_language
from app.models.professional_profile import AvailabilityStatus, VerificationStatus


class ServiceAreaInput(BaseModel):
    state: str | None = None
    district: str | None = None
    taluk: str | None = None
    village: str | None = None
    approx_latitude: float | None = None
    approx_longitude: float | None = None
    radius_km: float | None = None


class ProfessionalRegisterRequest(BaseModel):
    role: str
    display_name: str = Field(min_length=2, max_length=200)
    organization: str | None = None
    qualification: str | None = None
    experience_years: int | None = Field(default=None, ge=0, le=80)
    language_codes: list[str] = Field(default_factory=list)
    crop_specialization_ids: list[uuid.UUID] = Field(default_factory=list)
    disease_specialization_categories: list[str] = Field(default_factory=list)
    service_area: ServiceAreaInput | None = None

    @field_validator("language_codes")
    @classmethod
    def validate_languages(cls, v: list[str]) -> list[str]:
        for code in v:
            if not is_supported_language(code):
                raise ValueError(f"Unsupported language code: {code}")
        return v


class ProfessionalProfileResponse(BaseModel):
    id: uuid.UUID
    role: str
    display_name: str
    organization: str | None
    qualification: str | None
    experience_years: int | None
    language_codes: list[str] | None
    crop_specialization_ids: list[str] | None
    disease_specialization_categories: list[str] | None
    service_area: dict | None
    verification_status: VerificationStatus
    availability_status: AvailabilityStatus
    completed_case_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfessionalListResponse(BaseModel):
    items: list[ProfessionalProfileResponse]
    total: int


class AvailabilityUpdateRequest(BaseModel):
    availability_status: AvailabilityStatus


class VerificationActionRequest(BaseModel):
    reason: str | None = None

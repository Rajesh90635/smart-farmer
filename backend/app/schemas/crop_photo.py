import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.crop_photo import ImageQualityStatus, PhotoSource, UploadStatus


class CropPhotoSessionCreateRequest(BaseModel):
    crop_cycle_id: uuid.UUID
    label: str | None = Field(default=None, max_length=150)


class CropPhotoSessionResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    label: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropPhotoResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    original_filename: str | None
    mime_type: str
    file_size_bytes: int
    width_px: int
    height_px: int
    capture_timestamp: datetime | None
    upload_timestamp: datetime
    latitude: Decimal | None
    longitude: Decimal | None
    device_model: str | None
    capture_condition: str | None
    source: PhotoSource
    upload_status: UploadStatus
    image_quality_status: ImageQualityStatus
    quality_reasons: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("quality_reasons", mode="before")
    @classmethod
    def split_reasons(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [r for r in v.split(",") if r]
        return v


class CropPhotoListResponse(BaseModel):
    items: list[CropPhotoResponse]
    total: int


class DeadLetterReportCreateRequest(BaseModel):
    """D87-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    client_upload_id: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class DeadLetterReportResponse(BaseModel):
    id: uuid.UUID
    farmer_id: uuid.UUID
    client_upload_id: str
    reason: str
    reported_at: datetime

    model_config = {"from_attributes": True}


class DeadLetterReportListResponse(BaseModel):
    items: list[DeadLetterReportResponse]
    total: int


class PhotoUploadMetadata(BaseModel):
    """Multipart form fields accompanying the file itself. FastAPI binds
    these from Form(...) fields, not JSON body, since this is a
    multipart/form-data endpoint."""

    client_upload_id: str = Field(min_length=1, max_length=100)
    source: PhotoSource
    share_location: bool = False
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    # D91-03 (docs/audit/FINAL_CANONICAL_group_D.md): optional, client-
    # reported only - never inferred/guessed server-side.
    device_model: str | None = Field(default=None, max_length=150)
    capture_condition: str | None = Field(default=None, max_length=30)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("longitude must be between -180 and 180")
        return v

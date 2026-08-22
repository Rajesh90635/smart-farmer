import uuid
from datetime import datetime

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    """A single real, dated fact - never a fabricated or interpreted
    conclusion. event_type is a fixed enum-like string (documented in
    the service), never an arbitrary label. source_id always points to
    a real row in an existing table - this schema introduces no new
    persistence of its own."""
    event_type: str
    event_datetime: datetime
    title: str
    description: str
    source_id: uuid.UUID
    health_status: str | None = None
    treatment_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    photo_id: uuid.UUID | None = None
    analysis_id: uuid.UUID | None = None


class CropHealthTimelineResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    events: list[TimelineEvent]

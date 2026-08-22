import uuid

from pydantic import BaseModel


class IrrigationIntelligenceResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    recommendation: str
    reason: str
    weather_status: str
    pending_irrigation_task_id: uuid.UUID | None
    soil_moisture_available: bool
    is_deterministic: bool = True

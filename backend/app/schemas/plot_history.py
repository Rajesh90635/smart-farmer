import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.plot import SoilCategory, WaterAvailability


class PlotSoilHistoryResponse(BaseModel):
    id: uuid.UUID
    plot_id: uuid.UUID
    soil_type: str | None
    soil_category: SoilCategory | None
    changed_at: datetime

    model_config = {"from_attributes": True}


class PlotSoilHistoryListResponse(BaseModel):
    items: list[PlotSoilHistoryResponse]
    total: int


class PlotWaterHistoryResponse(BaseModel):
    id: uuid.UUID
    plot_id: uuid.UUID
    water_availability: WaterAvailability
    changed_at: datetime

    model_config = {"from_attributes": True}


class PlotWaterHistoryListResponse(BaseModel):
    items: list[PlotWaterHistoryResponse]
    total: int

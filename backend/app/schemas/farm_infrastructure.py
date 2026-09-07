import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.farm_infrastructure import FarmInfrastructureType


class FarmInfrastructureCreateRequest(BaseModel):
    infrastructure_type: FarmInfrastructureType
    description: str | None = Field(default=None, max_length=500)


class FarmInfrastructureResponse(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID
    infrastructure_type: FarmInfrastructureType
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmInfrastructureListResponse(BaseModel):
    items: list[FarmInfrastructureResponse]
    total: int

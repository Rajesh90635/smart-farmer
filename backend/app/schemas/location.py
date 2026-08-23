from pydantic import BaseModel


class StateResponse(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class DistrictResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MandalResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class VillageResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}

from pydantic import BaseModel

from app.schemas.crop import CropCycleResponse


class FarmerDashboardResponse(BaseModel):
    farm_count: int
    plot_count: int
    active_crop_cycle_count: int
    crops_nearing_harvest: list[CropCycleResponse]

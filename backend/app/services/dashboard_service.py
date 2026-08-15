import uuid

from sqlalchemy.orm import Session

from app.repositories import crop_cycle_repository, farm_repository, plot_repository
from app.schemas.crop import CropCycleResponse
from app.schemas.dashboard import FarmerDashboardResponse

_HARVEST_HORIZON_DAYS = 14
_MAX_NEARING_HARVEST = 10


def get_dashboard(db: Session, farmer_id: str) -> FarmerDashboardResponse:
    farmer_uuid = uuid.UUID(farmer_id)

    farm_count = farm_repository.count_active_for_farmer(db, farmer_uuid)
    plot_count = plot_repository.count_active_for_farmer(db, farmer_uuid)
    active_crop_cycle_count = crop_cycle_repository.count_active_for_farmer(db, farmer_uuid)
    nearing_harvest = crop_cycle_repository.list_nearing_harvest_for_farmer(
        db, farmer_uuid, within_days=_HARVEST_HORIZON_DAYS, limit=_MAX_NEARING_HARVEST
    )

    return FarmerDashboardResponse(
        farm_count=farm_count,
        plot_count=plot_count,
        active_crop_cycle_count=active_crop_cycle_count,
        crops_nearing_harvest=[CropCycleResponse.model_validate(c) for c in nearing_harvest],
    )

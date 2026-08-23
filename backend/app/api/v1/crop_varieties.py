"""
CropVariety endpoint: read-only listing of varieties for a crop, to
populate the variety dropdown after a farmer selects a crop. Reference
data (not farmer-owned), so no ownership check - same pattern as
GET /crops/master.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.crop_variety import CropVarietyResponse
from app.services import crop_variety_service

router = APIRouter(tags=["crop-varieties"])


@router.get("/crops/{crop_id}/varieties", response_model=list[CropVarietyResponse])
def list_crop_varieties(
    crop_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> list[CropVarietyResponse]:
    return crop_variety_service.list_varieties_for_crop(db, crop_id)

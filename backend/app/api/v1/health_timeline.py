"""
Phase 35 endpoint: crop health timeline.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.health_timeline import CropHealthTimelineResponse
from app.services import health_timeline_service

router = APIRouter(tags=["health-timeline"])


@router.get("/crop-cycles/{crop_cycle_id}/health-timeline", response_model=CropHealthTimelineResponse)
def get_health_timeline(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropHealthTimelineResponse:
    return health_timeline_service.get_health_timeline(db, current_user.user_id, crop_cycle_id)

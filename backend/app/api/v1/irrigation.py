"""D18-06: irrigation activity record endpoints."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.irrigation import IrrigationRecordCreateRequest, IrrigationRecordListResponse, IrrigationRecordResponse
from app.services import irrigation_service

router = APIRouter(tags=["irrigation"])


@router.post("/crop-cycles/{crop_cycle_id}/irrigation-records", response_model=IrrigationRecordResponse, status_code=201)
def create_irrigation_record(
    crop_cycle_id: uuid.UUID,
    payload: IrrigationRecordCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> IrrigationRecordResponse:
    return irrigation_service.create_irrigation_record(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/irrigation-records", response_model=IrrigationRecordListResponse)
def list_irrigation_records(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> IrrigationRecordListResponse:
    return irrigation_service.list_irrigation_records(db, current_user.user_id, crop_cycle_id)

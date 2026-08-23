"""
Farm endpoints. Every route resolves the farm via the CALLER's own
farmer_id (see app/services/farm_service.py) - there is no admin-style
"get any farm by id" route here, so cross-farmer access isn't just
checked-for, it's structurally impossible in this router.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.farm import FarmCreateRequest, FarmListResponse, FarmResponse, FarmUpdateRequest
from app.services import farm_service

router = APIRouter(prefix="/farms", tags=["farms"])


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmResponse:
    return farm_service.create_farm(db, current_user.user_id, payload)


@router.get("", response_model=FarmListResponse)
def list_my_farms(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmListResponse:
    return farm_service.list_my_farms(db, current_user.user_id, limit=limit, offset=offset)


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmResponse:
    return farm_service.get_my_farm(db, current_user.user_id, farm_id)


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: uuid.UUID,
    payload: FarmUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmResponse:
    return farm_service.update_my_farm(db, current_user.user_id, farm_id, payload)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_farm(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    # Soft delete (status -> INACTIVE), not a real DELETE - see
    # farm_service.deactivate_my_farm's docstring for why. Modeled as HTTP
    # DELETE anyway since that's the semantically correct verb from the
    # client's point of view ("remove this farm from my active list").
    farm_service.deactivate_my_farm(db, current_user.user_id, farm_id)

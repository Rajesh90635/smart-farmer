"""D2-07 (docs/audit/FINAL_CANONICAL_group_A.md): farm infrastructure endpoints."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.farm_infrastructure import FarmInfrastructureCreateRequest, FarmInfrastructureListResponse, FarmInfrastructureResponse
from app.services import farm_infrastructure_service

router = APIRouter(tags=["farm-infrastructure"])


@router.post("/farms/{farm_id}/infrastructure", response_model=FarmInfrastructureResponse, status_code=status.HTTP_201_CREATED)
def create_farm_infrastructure(
    farm_id: uuid.UUID,
    payload: FarmInfrastructureCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmInfrastructureResponse:
    return farm_infrastructure_service.create_infrastructure(db, current_user.user_id, farm_id, payload)


@router.get("/farms/{farm_id}/infrastructure", response_model=FarmInfrastructureListResponse)
def list_farm_infrastructure(
    farm_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FarmInfrastructureListResponse:
    return farm_infrastructure_service.list_infrastructure_for_farm(db, current_user.user_id, farm_id, limit=limit, offset=offset)


@router.delete("/farms/{farm_id}/infrastructure/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm_infrastructure(
    farm_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    farm_infrastructure_service.delete_infrastructure(db, current_user.user_id, farm_id, item_id)

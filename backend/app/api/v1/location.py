"""
Location master-data endpoints: read-only state/district/mandal/village
reference data for farm/farmer location dropdowns (see
app/models/location.py). No write endpoints - this data is seeded via
migration (states/districts) or managed later the same way
(mandals/villages, currently empty - no authoritative dataset exists yet).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import SEEDED_ROLE_CODES
from app.db.session import get_db
from app.schemas.location import DistrictResponse, MandalResponse, StateResponse, VillageResponse
from app.services import location_service

router = APIRouter(prefix="/states", tags=["location"])
district_router = APIRouter(prefix="/districts", tags=["location"])
mandal_router = APIRouter(prefix="/mandals", tags=["location"])

_ANY_SEEDED_ROLE = [role.value for role in SEEDED_ROLE_CODES]


@router.get("", response_model=list[StateResponse])
def list_states(
    current_user: CurrentUser = Depends(require_role(*_ANY_SEEDED_ROLE)),
    db: Session = Depends(get_db),
) -> list[StateResponse]:
    return location_service.list_states(db)


@router.get("/{state_id}/districts", response_model=list[DistrictResponse])
def list_districts(
    state_id: int,
    current_user: CurrentUser = Depends(require_role(*_ANY_SEEDED_ROLE)),
    db: Session = Depends(get_db),
) -> list[DistrictResponse]:
    return location_service.list_districts_for_state(db, state_id)


@district_router.get("/{district_id}/mandals", response_model=list[MandalResponse])
def list_mandals(
    district_id: int,
    current_user: CurrentUser = Depends(require_role(*_ANY_SEEDED_ROLE)),
    db: Session = Depends(get_db),
) -> list[MandalResponse]:
    return location_service.list_mandals_for_district(db, district_id)


@mandal_router.get("/{mandal_id}/villages", response_model=list[VillageResponse])
def list_villages(
    mandal_id: int,
    current_user: CurrentUser = Depends(require_role(*_ANY_SEEDED_ROLE)),
    db: Session = Depends(get_db),
) -> list[VillageResponse]:
    return location_service.list_villages_for_mandal(db, mandal_id)

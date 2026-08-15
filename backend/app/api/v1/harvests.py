"""
Harvest management + farmer harvest listings.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.harvest import (
    HarvestConfirmReadyRequest,
    HarvestListingCreateRequest,
    HarvestListingListResponse,
    HarvestListingResponse,
    HarvestListResponse,
    HarvestResponse,
)
from app.services import harvest_service

router = APIRouter(prefix="/harvests", tags=["harvests"])


@router.post("/from-crop-cycle/{crop_cycle_id}", response_model=HarvestResponse, status_code=201)
def get_or_create_harvest(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> HarvestResponse:
    """'Smart listing' pre-fill - reuses the existing crop cycle's data."""
    return harvest_service.get_or_create_harvest_for_crop_cycle(db, current_user.user_id, crop_cycle_id)


@router.get("", response_model=HarvestListResponse)
def list_my_harvests(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> HarvestListResponse:
    return harvest_service.list_my_harvests(db, current_user.user_id, limit=limit, offset=offset)


@router.post("/{harvest_id}/approaching", response_model=HarvestResponse)
def mark_approaching(
    harvest_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> HarvestResponse:
    return harvest_service.mark_approaching(db, current_user.user_id, harvest_id)


@router.post("/{harvest_id}/confirm-ready", response_model=HarvestResponse)
def confirm_ready(
    harvest_id: uuid.UUID,
    payload: HarvestConfirmReadyRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> HarvestResponse:
    """The ONLY way a harvest reaches READY - always an explicit farmer action."""
    return harvest_service.confirm_ready(db, current_user.user_id, harvest_id, payload)


@router.post("/{harvest_id}/listing", response_model=HarvestListingResponse, status_code=201)
def create_listing(
    harvest_id: uuid.UUID,
    payload: HarvestListingCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> HarvestListingResponse:
    return harvest_service.create_listing(db, current_user.user_id, harvest_id, payload)


@router.get("/listings/me", response_model=HarvestListingListResponse)
def list_my_listings(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> HarvestListingListResponse:
    return harvest_service.list_my_listings(db, current_user.user_id, limit=limit, offset=offset)

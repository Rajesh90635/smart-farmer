"""
Farmer input inventory endpoints (Domains 21-24) - the farmer's own
on-farm stock, separate from the marketplace/dealer side.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.input_inventory import (
    InputInventoryItemCreateRequest,
    InputInventoryItemResponse,
    InputInventoryListResponse,
    QuantityCorrectionRequest,
    RestockRequest,
    UsageRecordRequest,
)
from app.services import input_inventory_service

router = APIRouter(tags=["input-inventory"])


@router.post("/input-inventory", response_model=InputInventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: InputInventoryItemCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputInventoryItemResponse:
    return input_inventory_service.create_item(db, current_user.user_id, payload)


@router.get("/input-inventory", response_model=InputInventoryListResponse)
def list_items(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputInventoryListResponse:
    return input_inventory_service.list_items(db, current_user.user_id)


@router.get("/input-inventory/{item_id}", response_model=InputInventoryItemResponse)
def get_item(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputInventoryItemResponse:
    return input_inventory_service.get_item(db, current_user.user_id, item_id)


@router.post("/input-inventory/{item_id}/usage", response_model=InputInventoryItemResponse)
def record_usage(
    item_id: uuid.UUID,
    payload: UsageRecordRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputInventoryItemResponse:
    return input_inventory_service.record_usage(db, current_user.user_id, item_id, payload)


@router.post("/input-inventory/{item_id}/restock", response_model=InputInventoryItemResponse)
def restock(
    item_id: uuid.UUID,
    payload: RestockRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputInventoryItemResponse:
    return input_inventory_service.restock(db, current_user.user_id, item_id, payload)


@router.post("/input-inventory/{item_id}/correct", response_model=InputInventoryItemResponse)
def correct_quantity(
    item_id: uuid.UUID,
    payload: QuantityCorrectionRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InputInventoryItemResponse:
    return input_inventory_service.correct_quantity(db, current_user.user_id, item_id, payload)

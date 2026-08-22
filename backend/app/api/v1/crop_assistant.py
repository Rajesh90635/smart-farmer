"""
Phase 36 endpoint: crop-cycle-scoped AI assistant.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.crop_assistant import CropAssistantRequest, CropAssistantResponse
from app.services import crop_assistant_service

router = APIRouter(tags=["crop-assistant"])


@router.post("/crop-cycles/{crop_cycle_id}/assistant", response_model=CropAssistantResponse)
def ask_crop_assistant(
    crop_cycle_id: uuid.UUID,
    payload: CropAssistantRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CropAssistantResponse:
    return crop_assistant_service.ask_crop_assistant(db, current_user.user_id, crop_cycle_id, payload, settings)

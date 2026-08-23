"""
Crop photo endpoints: sessions, upload, list, detail, file serving,
delete. Every route resolves ownership via the CALLER's own farmer_id -
no route accepts an arbitrary farmer id, matching the pattern already
established for Farm/Plot/CropCycle.

File bytes are served through an authenticated endpoint
(/crop-photos/{id}/file), never a public static path - see
docs/CROP_PHOTO_MODULE.md "Privacy" section for why.
"""
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core import error_codes
from app.core.roles import Role
from app.core.storage_dependency import get_file_storage
from app.core.ai_model_dependency import get_model_provider
from app.db.session import get_db
from app.models.crop_photo import PhotoSource
from app.schemas.ai_analysis import AIAnalysisListResponse, AIAnalysisResponse
from app.schemas.crop_photo import (
    CropPhotoListResponse,
    CropPhotoResponse,
    CropPhotoSessionCreateRequest,
    CropPhotoSessionResponse,
    PhotoUploadMetadata,
)
from app.services import ai_analysis_service, crop_photo_service
from app.services.ai.model_provider import ModelProvider
from app.services.storage.base import FileStorage

router = APIRouter(tags=["crop-photos"])


@router.post("/crop-photo-sessions", response_model=CropPhotoSessionResponse, status_code=status.HTTP_201_CREATED)
def create_photo_session(
    payload: CropPhotoSessionCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropPhotoSessionResponse:
    return crop_photo_service.create_session(db, current_user.user_id, payload)


@router.get("/crop-photo-sessions/{session_id}", response_model=CropPhotoSessionResponse)
def get_photo_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropPhotoSessionResponse:
    return crop_photo_service.get_session(db, current_user.user_id, session_id)


@router.post(
    "/crop-photo-sessions/{session_id}/photos", response_model=CropPhotoResponse, status_code=status.HTTP_201_CREATED
)
async def upload_photo(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    client_upload_id: str = Form(...),
    source: PhotoSource = Form(...),
    share_location: bool = Form(False),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
    settings: Settings = Depends(get_settings),
) -> CropPhotoResponse:
    if not file.content_type:
        raise AppError(error_codes.VALIDATION_ERROR, "Missing file content type.", 422)

    content = await file.read()
    metadata = PhotoUploadMetadata(
        client_upload_id=client_upload_id,
        source=source,
        share_location=share_location,
        latitude=latitude,
        longitude=longitude,
    )

    return crop_photo_service.upload_photo(
        db,
        current_user.user_id,
        session_id,
        metadata,
        content,
        file.content_type,
        file.filename,
        storage,
        settings,
    )


@router.get("/crop-cycles/{crop_cycle_id}/photos", response_model=CropPhotoListResponse)
def list_photos_for_crop_cycle(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropPhotoListResponse:
    return crop_photo_service.list_photos_for_crop_cycle(db, current_user.user_id, crop_cycle_id)


@router.get("/crop-photos/{photo_id}", response_model=CropPhotoResponse)
def get_photo(
    photo_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropPhotoResponse:
    return crop_photo_service.get_photo(db, current_user.user_id, photo_id)


@router.get("/crop-photos/{photo_id}/file")
def get_photo_file(
    photo_id: uuid.UUID,
    thumbnail: bool = Query(default=False),
    # Broadened from farmer-only to also allow field agents/experts with a
    # valid case-based PhotoAccessGrant - see
    # crop_photo_service.get_photo_for_serving_authorized for the actual
    # authorization check (farmer ownership OR an active grant).
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value, Role.FIELD_AGENT.value, Role.EXPERT.value)),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
) -> StreamingResponse:
    photo, storage_key = crop_photo_service.get_photo_for_serving_authorized(
        db, current_user, photo_id, thumbnail=thumbnail
    )
    file_stream = storage.open_read(storage_key)
    return StreamingResponse(file_stream, media_type=photo.mime_type)


@router.delete("/crop-photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    crop_photo_service.delete_photo(db, current_user.user_id, photo_id)


@router.post("/crop-photos/{photo_id}/analyze", response_model=AIAnalysisResponse, status_code=status.HTTP_201_CREATED)
def analyze_photo(
    photo_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    model_provider: ModelProvider = Depends(get_model_provider),
    storage: FileStorage = Depends(get_file_storage),
    settings: Settings = Depends(get_settings),
) -> AIAnalysisResponse:
    return ai_analysis_service.analyze_photo(db, current_user.user_id, photo_id, model_provider, storage, settings)


@router.get("/crop-photos/{photo_id}/analysis", response_model=AIAnalysisResponse)
def get_photo_analysis(
    photo_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> AIAnalysisResponse:
    return ai_analysis_service.get_latest_for_photo(db, current_user.user_id, photo_id)


@router.get("/crop-cycles/{crop_cycle_id}/analyses", response_model=AIAnalysisListResponse)
def list_analyses_for_crop_cycle(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> AIAnalysisListResponse:
    return ai_analysis_service.list_for_crop_cycle(db, current_user.user_id, crop_cycle_id)

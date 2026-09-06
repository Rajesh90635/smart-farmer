"""D20-01..12: Soil Testing domain endpoints."""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.storage_dependency import get_file_storage
from app.db.session import get_db
from app.schemas.soil_testing import (
    SoilSampleCreateRequest,
    SoilSampleListResponse,
    SoilSampleResponse,
    SoilTestResultCreateRequest,
    SoilTestResultListResponse,
    SoilTestResultResponse,
)
from app.services import soil_testing_service
from app.services.storage.base import FileStorage

router = APIRouter(tags=["soil-testing"])


@router.post("/plots/{plot_id}/soil-samples", response_model=SoilSampleResponse, status_code=201)
def create_soil_sample(
    plot_id: uuid.UUID,
    payload: SoilSampleCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SoilSampleResponse:
    return soil_testing_service.create_soil_sample(db, current_user.user_id, plot_id, payload)


@router.get("/plots/{plot_id}/soil-samples", response_model=SoilSampleListResponse)
def list_soil_samples(
    plot_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> SoilSampleListResponse:
    return soil_testing_service.list_soil_samples(db, current_user.user_id, plot_id)


@router.post("/soil-samples/{sample_id}/results", response_model=SoilTestResultResponse, status_code=201)
def create_soil_test_result(
    sample_id: uuid.UUID,
    payload: SoilTestResultCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SoilTestResultResponse:
    return soil_testing_service.create_soil_test_result(db, current_user.user_id, sample_id, payload, settings)


@router.get("/soil-samples/{sample_id}/results", response_model=SoilTestResultListResponse)
def list_soil_test_results(
    sample_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SoilTestResultListResponse:
    return soil_testing_service.list_soil_test_results(db, current_user.user_id, sample_id, settings)


@router.post("/soil-test-results/{result_id}/report", response_model=SoilTestResultResponse, status_code=201)
async def upload_soil_report(
    result_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
    settings: Settings = Depends(get_settings),
) -> SoilTestResultResponse:
    file_bytes = await file.read()
    return soil_testing_service.upload_soil_report(
        db, current_user.user_id, result_id, file_bytes, file.filename or "soil_report.jpg",
        file.content_type or "image/jpeg", storage, settings,
    )

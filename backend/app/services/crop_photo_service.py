import uuid
from datetime import datetime, timezone
from io import BytesIO

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.image_processing import process_image
from app.core.image_quality import check_quality
from app.core.image_validation import validate_upload
from app.core.photo_storage_keys import build_leaf_filename, build_photo_container
from app.middleware.rate_limit import InMemoryRateLimiter
from app.models.crop_photo import CropPhoto, ImageQualityStatus, UploadStatus
from app.models.crop_photo_session import CropPhotoSession
from app.repositories import crop_cycle_repository, crop_photo_repository, crop_photo_session_repository
from app.schemas.crop_photo import (
    CropPhotoListResponse,
    CropPhotoResponse,
    CropPhotoSessionCreateRequest,
    CropPhotoSessionResponse,
    PhotoUploadMetadata,
)
from app.services.audit_logger import AuditLogger
from app.services.storage.base import FileStorage

_EXT_BY_MIME = {"image/jpeg": "jpg", "image/png": "jpg", "image/webp": "jpg"}
# Note: everything is re-encoded to JPEG during processing (see
# image_processing.py) regardless of the uploaded format, so the stored
# file's extension is always "jpg" - deliberate simplification, not an
# oversight. PNG/WEBP are accepted as *input* formats only.

# D100-14 (docs/audit/c13_governance_farmbrain_security.md): rate_limit.py's
# own docstring named "image-upload endpoints" as an intended target from
# the start, but nothing ever wired it in here - confirmed by grep before
# this fix. Keyed by farmer_id (an account-level cost/abuse bound, not an
# IP-level one - a farmer legitimately taking several photos in one
# session must not be blocked by a same-IP household/shared-network
# limiter).
_upload_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=300)


def create_session(db: Session, farmer_id: str, payload: CropPhotoSessionCreateRequest) -> CropPhotoSessionResponse:
    crop_cycle = crop_cycle_repository.get_owned(db, payload.crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    session_obj = CropPhotoSession(
        crop_cycle_id=payload.crop_cycle_id,
        farmer_id=uuid.UUID(farmer_id),
        label=payload.label,
    )
    crop_photo_session_repository.create(db, session_obj)
    db.flush()

    AuditLogger(db).log(
        "CROP_PHOTO_SESSION_CREATED",
        actor_id=farmer_id,
        actor_role="farmer",
        entity="crop_photo_session",
        entity_id=str(session_obj.id),
    )

    db.commit()
    db.refresh(session_obj)
    return CropPhotoSessionResponse.model_validate(session_obj)


def get_session(db: Session, farmer_id: str, session_id: uuid.UUID) -> CropPhotoSessionResponse:
    session_obj = crop_photo_session_repository.get_owned(db, session_id, uuid.UUID(farmer_id))
    if session_obj is None:
        raise AppError(error_codes.NOT_FOUND, "Photo session not found.", 404)
    return CropPhotoSessionResponse.model_validate(session_obj)


def upload_photo(
    db: Session,
    farmer_id: str,
    session_id: uuid.UUID,
    metadata: PhotoUploadMetadata,
    file_content: bytes,
    declared_mime_type: str,
    original_filename: str | None,
    storage: FileStorage,
    settings: Settings,
) -> CropPhotoResponse:
    if not _upload_limiter.allow(farmer_id):
        raise AppError(error_codes.RATE_LIMITED, "Too many photo uploads. Please wait a few minutes and try again.", 429)

    farmer_uuid = uuid.UUID(farmer_id)

    session_obj = crop_photo_session_repository.get_owned(db, session_id, farmer_uuid)
    if session_obj is None:
        raise AppError(error_codes.NOT_FOUND, "Photo session not found.", 404)

    existing = crop_photo_repository.get_by_client_upload_id(db, session_id, metadata.client_upload_id)
    if existing is not None:
        return CropPhotoResponse.model_validate(existing)

    crop_cycle = crop_cycle_repository.get_owned(db, session_obj.crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    validated = validate_upload(content=file_content, declared_mime_type=declared_mime_type, settings=settings)
    processed = process_image(validated.image, settings=settings)
    quality = check_quality(validated.image, settings)

    extension = _EXT_BY_MIME.get(declared_mime_type, "jpg")
    container = build_photo_container(farmer_id=farmer_uuid, crop_cycle_id=crop_cycle.id)

    # Each save() call generates and returns its OWN unique key - captured
    # and persisted here, never pre-computed and assumed. This was a real
    # bug during development: pre-computing a key and discarding save()'s
    # actual return value meant the DB pointed at a path that didn't match
    # where the file was really written. See docs/IMAGE_STORAGE.md.
    storage_key = storage.save(
        container, build_leaf_filename(extension=extension), BytesIO(processed.content), "image/jpeg"
    )
    thumbnail_key = storage.save(
        container, build_leaf_filename(extension=extension), BytesIO(processed.thumbnail_content), "image/jpeg"
    )

    photo = CropPhoto(
        session_id=session_id,
        crop_cycle_id=crop_cycle.id,
        plot_id=crop_cycle.plot_id,
        farm_id=crop_cycle.plot.farm_id,
        farmer_id=farmer_uuid,
        client_upload_id=metadata.client_upload_id,
        storage_key=storage_key,
        thumbnail_storage_key=thumbnail_key,
        original_filename=_sanitize_display_filename(original_filename),
        file_extension=extension,
        mime_type="image/jpeg",
        file_size_bytes=len(processed.content),
        width_px=processed.width,
        height_px=processed.height,
        upload_timestamp=datetime.now(timezone.utc),
        latitude=metadata.latitude if metadata.share_location else None,
        longitude=metadata.longitude if metadata.share_location else None,
        source=metadata.source,
        upload_status=UploadStatus.READY,
        image_quality_status=ImageQualityStatus.ACCEPTED if quality.accepted else ImageQualityStatus.REJECTED,
        quality_reasons=",".join(quality.reasons) if quality.reasons else None,
    )
    crop_photo_repository.create(db, photo)
    db.flush()

    AuditLogger(db).log(
        "CROP_PHOTO_UPLOADED", actor_id=farmer_id, actor_role="farmer", entity="crop_photo", entity_id=str(photo.id)
    )

    db.commit()
    db.refresh(photo)
    return CropPhotoResponse.model_validate(photo)


def list_photos_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropPhotoListResponse:
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, uuid.UUID(farmer_id))
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    photos = crop_photo_repository.list_for_crop_cycle(db, crop_cycle_id, uuid.UUID(farmer_id))
    return CropPhotoListResponse(items=[CropPhotoResponse.model_validate(p) for p in photos], total=len(photos))


def get_photo(db: Session, farmer_id: str, photo_id: uuid.UUID) -> CropPhotoResponse:
    photo = crop_photo_repository.get_owned(db, photo_id, uuid.UUID(farmer_id))
    if photo is None:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)
    return CropPhotoResponse.model_validate(photo)


def get_photo_for_serving(db: Session, farmer_id: str, photo_id: uuid.UUID, *, thumbnail: bool) -> tuple[CropPhoto, str]:
    """Returns (photo, storage_key) for the caller to stream from storage.
    Never returns a public URL - the file is only reachable through this
    authenticated, ownership-checked endpoint."""
    photo = crop_photo_repository.get_owned(db, photo_id, uuid.UUID(farmer_id))
    if photo is None:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)
    key = photo.thumbnail_storage_key if (thumbnail and photo.thumbnail_storage_key) else photo.storage_key
    return photo, key


def get_photo_for_serving_authorized(db: Session, current_user, photo_id: uuid.UUID, *, thumbnail: bool) -> tuple[CropPhoto, str]:
    """Extends farmer-ownership photo access (above) with a second,
    equally-authoritative path: a professional with a valid, non-expired,
    non-revoked PhotoAccessGrant for this exact photo (Professional
    Network phase). No new photo-serving endpoint was built for this -
    the EXISTING endpoint's authorization is broadened, per "do not
    duplicate infrastructure."
    """
    from app.core.roles import Role
    from app.repositories import case_repository, professional_repository

    if current_user.role == Role.FARMER.value:
        return get_photo_for_serving(db, current_user.user_id, photo_id, thumbnail=thumbnail)

    professional = professional_repository.get_by_user_id(db, uuid.UUID(current_user.user_id))
    if professional is None:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)

    grant = case_repository.get_active_grant(db, photo_id, professional.id)
    if grant is None:
        # Same 404-not-403 ID-enumeration defense used everywhere else in
        # this codebase - "not authorized" and "doesn't exist" must look
        # identical from the caller's side.
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)

    photo = db.get(CropPhoto, photo_id)
    if photo is None or photo.upload_status == UploadStatus.DELETED:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)

    # Photo access audit (Requirement 29) - who, when, why, case id. Never
    # logs the image itself.
    AuditLogger(db).log(
        "CASE_PHOTO_ACCESSED",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        entity="crop_health_case",
        entity_id=str(grant.case_id),
    )
    db.commit()

    key = photo.thumbnail_storage_key if (thumbnail and photo.thumbnail_storage_key) else photo.storage_key
    return photo, key


def delete_photo(db: Session, farmer_id: str, photo_id: uuid.UUID) -> None:
    photo = crop_photo_repository.get_owned(db, photo_id, uuid.UUID(farmer_id))
    if photo is None:
        raise AppError(error_codes.NOT_FOUND, "Photo not found.", 404)

    # Soft delete only - the underlying files and DB row are left intact
    # so a future AI/audit workflow that already reasoned about this photo
    # doesn't silently lose its subject. upload_status=DELETED excludes it
    # from every normal listing/retrieval path (see repository queries).
    photo.upload_status = UploadStatus.DELETED

    AuditLogger(db).log(
        "CROP_PHOTO_DELETED", actor_id=farmer_id, actor_role="farmer", entity="crop_photo", entity_id=str(photo.id)
    )

    db.commit()


def _sanitize_display_filename(filename: str | None) -> str | None:
    """Kept ONLY for farmer-facing display - never used to build a storage
    path. Strips path separators and collapses ".." sequences a hostile
    client might have included - not a security boundary (this value never
    touches the filesystem), just avoids ugly/confusing display text."""
    if not filename:
        return None
    cleaned = filename.replace("/", "_").replace("\\", "_").replace("..", "_").strip()
    return cleaned[:255] or None

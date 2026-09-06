"""
D67-03 (docs/audit/FINAL_CANONICAL_group_C.md): dispute-evidence image
storage, shared by both dispute types (OrderDispute, SaleDispute). A
DELIBERATELY separate pipeline from crop-photo's (own container prefix,
own storage-key column per dispute type) - reuses only the underlying
validate_upload/process_image/FileStorage building blocks, per this
row's own citation of why the two domains should stay independent.
"""
import uuid
from io import BytesIO

from app.core.config import Settings
from app.core.image_processing import process_image
from app.core.image_validation import validate_upload
from app.services.storage.base import FileStorage

_EXT_BY_MIME = {"image/jpeg": "jpg", "image/png": "jpg", "image/webp": "jpg"}


def _build_container(*, dispute_id: uuid.UUID) -> str:
    return f"dispute-evidence/{dispute_id}"


def _build_leaf_filename(*, extension: str) -> str:
    return f"{uuid.uuid4().hex}.{extension}"


def store_evidence_image(
    file_content: bytes, declared_mime_type: str, dispute_id: uuid.UUID, storage: FileStorage, settings: Settings
) -> str:
    validated = validate_upload(content=file_content, declared_mime_type=declared_mime_type, settings=settings)
    processed = process_image(validated.image, settings=settings)
    extension = _EXT_BY_MIME.get(declared_mime_type, "jpg")
    container = _build_container(dispute_id=dispute_id)
    return storage.save(container, _build_leaf_filename(extension=extension), BytesIO(processed.content), "image/jpeg")

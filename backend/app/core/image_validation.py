"""
Image validation (Requirement 6). Purely technical checks - never an
agricultural judgment. Raises AppError with a farmer-safe message on any
failure; callers don't need their own try/except per rule.
"""
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError

_MIME_TO_PIL_FORMAT = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


@dataclass(frozen=True)
class ValidatedImage:
    image: Image.Image
    width: int
    height: int
    detected_format: str  # Pillow's own format string, e.g. "JPEG"


def validate_upload(*, content: bytes, declared_mime_type: str, settings: Settings) -> ValidatedImage:
    if not content:
        raise AppError(error_codes.VALIDATION_ERROR, "The uploaded file is empty.", 422)

    if len(content) > settings.photo_max_upload_size_bytes:
        max_mb = settings.photo_max_upload_size_bytes / (1024 * 1024)
        raise AppError(error_codes.VALIDATION_ERROR, f"Photo is too large. Maximum size is {max_mb:.0f} MB.", 422)

    if declared_mime_type not in settings.photo_allowed_mime_types:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            "Unsupported photo format. Please use JPEG, PNG, or WEBP.",
            422,
        )

    try:
        image = Image.open(BytesIO(content))
        image.verify()  # cheap corruption check - raises if the file is malformed
        # verify() leaves the image object unusable for further ops, so
        # reopen for actual dimension/format reads and later processing.
        image = Image.open(BytesIO(content))
        width, height = image.size
        detected_format = image.format
    except UnidentifiedImageError as exc:
        raise AppError(error_codes.VALIDATION_ERROR, "This does not appear to be a valid image file.", 422) from exc
    except Exception as exc:  # noqa: BLE001 - any other Pillow failure means "corrupted/unreadable", not a 500
        raise AppError(error_codes.VALIDATION_ERROR, "The photo appears to be corrupted. Please try again.", 422) from exc

    expected_format = _MIME_TO_PIL_FORMAT.get(declared_mime_type)
    if expected_format is not None and detected_format != expected_format:
        # The declared Content-Type doesn't match what the bytes actually
        # are (e.g. a renamed .exe with a fake image/jpeg header) - reject
        # rather than trust the client's claim.
        raise AppError(
            error_codes.VALIDATION_ERROR,
            "The photo's actual format doesn't match its declared type. Please try a different photo.",
            422,
        )

    if width < settings.photo_min_width_px or height < settings.photo_min_height_px:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            f"Photo is too small. Minimum size is {settings.photo_min_width_px}x{settings.photo_min_height_px} pixels.",
            422,
        )

    return ValidatedImage(image=image, width=width, height=height, detected_format=detected_format)

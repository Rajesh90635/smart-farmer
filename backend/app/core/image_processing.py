"""
Image processing (Requirement 14). Runs synchronously on the request
thread in this phase - deliberately kept cheap (Pillow resize/re-encode,
no ML) so this doesn't become a request-blocking problem. If a future
phase needs heavier processing, this is the seam to move behind a
background queue - the call site (crop_photo_service) doesn't need to
change, only what's behind this function.

Privacy: EXIF is stripped unconditionally on every stored image - consent
controls whether coordinates the farmer explicitly provided are stored in
the database, not whether embedded EXIF GPS survives into the file.
"""
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps

from app.core.config import Settings


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    width: int
    height: int
    thumbnail_content: bytes
    thumbnail_width: int
    thumbnail_height: int


def process_image(image: Image.Image, *, settings: Settings) -> ProcessedImage:
    # Normalize orientation using the EXIF Orientation tag BEFORE that tag
    # (and all other EXIF) is discarded - otherwise a photo taken in
    # portrait on a phone that only sets an EXIF rotation flag would be
    # stored sideways.
    normalized = ImageOps.exif_transpose(image)
    normalized = normalized.convert("RGB")  # ensures consistent encoding for PNG/WEBP inputs too

    resized = _resize_to_max_dimension(normalized, settings.photo_max_dimension_px)
    main_bytes = _encode_jpeg(resized, settings.photo_jpeg_quality)

    thumbnail = _resize_to_max_dimension(normalized, settings.photo_thumbnail_max_dimension_px)
    thumb_bytes = _encode_jpeg(thumbnail, settings.photo_jpeg_quality)

    return ProcessedImage(
        content=main_bytes,
        width=resized.width,
        height=resized.height,
        thumbnail_content=thumb_bytes,
        thumbnail_width=thumbnail.width,
        thumbnail_height=thumbnail.height,
    )


def _resize_to_max_dimension(image: Image.Image, max_dimension: int) -> Image.Image:
    width, height = image.size
    longest_side = max(width, height)
    if longest_side <= max_dimension:
        return image
    scale = max_dimension / longest_side
    return image.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.LANCZOS)


def _encode_jpeg(image: Image.Image, quality: int) -> bytes:
    buffer = BytesIO()
    # Pillow's default JPEG save with no exif= argument writes no EXIF
    # block at all - this IS the EXIF-stripping step, not a separate one.
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()

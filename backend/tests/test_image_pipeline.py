import pytest

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.image_processing import process_image
from app.core.image_quality import check_quality
from app.core.image_validation import validate_upload
from tests.photo_factories import make_test_jpeg, make_test_png

settings = get_settings()


def test_validate_accepts_a_good_jpeg():
    validated = validate_upload(content=make_test_jpeg(), declared_mime_type="image/jpeg", settings=settings)
    assert validated.width == 600
    assert validated.height == 600
    assert validated.detected_format == "JPEG"


def test_validate_accepts_a_good_png():
    validated = validate_upload(content=make_test_png(), declared_mime_type="image/png", settings=settings)
    assert validated.detected_format == "PNG"


def test_validate_rejects_empty_content():
    with pytest.raises(AppError):
        validate_upload(content=b"", declared_mime_type="image/jpeg", settings=settings)


def test_validate_rejects_corrupted_data():
    with pytest.raises(AppError) as exc_info:
        validate_upload(content=b"definitely not an image", declared_mime_type="image/jpeg", settings=settings)
    assert exc_info.value.status_code == 422


def test_validate_rejects_oversized_file():
    huge = b"\xff\xd8\xff" + b"\x00" * (settings.photo_max_upload_size_bytes + 1)
    with pytest.raises(AppError):
        validate_upload(content=huge, declared_mime_type="image/jpeg", settings=settings)


def test_validate_rejects_too_small_image():
    with pytest.raises(AppError):
        validate_upload(content=make_test_jpeg(width=100, height=100), declared_mime_type="image/jpeg", settings=settings)


def test_validate_rejects_mismatched_declared_type():
    # Real PNG bytes, but declared as JPEG - the actual format check must catch this.
    with pytest.raises(AppError):
        validate_upload(content=make_test_png(), declared_mime_type="image/jpeg", settings=settings)


def test_validate_rejects_unsupported_mime_type():
    with pytest.raises(AppError):
        validate_upload(content=make_test_jpeg(), declared_mime_type="application/pdf", settings=settings)


def test_quality_accepts_a_normal_midtone_image():
    validated = validate_upload(content=make_test_jpeg(color=(128, 128, 128)), declared_mime_type="image/jpeg", settings=settings)
    # A flat solid-color image has zero edge variance, so it will register
    # as "too_blurry" even though it's midtone brightness - use a noisy
    # image to isolate the brightness check.
    result = check_quality(validated.image, settings)
    assert "too_dark" not in result.reasons
    assert "too_bright" not in result.reasons


def test_quality_flags_too_dark():
    validated = validate_upload(content=make_test_jpeg(color=(2, 2, 2)), declared_mime_type="image/jpeg", settings=settings)
    result = check_quality(validated.image, settings)
    assert "too_dark" in result.reasons
    assert result.accepted is False


def test_quality_flags_too_bright():
    validated = validate_upload(content=make_test_jpeg(color=(253, 253, 253)), declared_mime_type="image/jpeg", settings=settings)
    result = check_quality(validated.image, settings)
    assert "too_bright" in result.reasons
    assert result.accepted is False


def test_quality_flags_flat_image_as_blurry():
    # A perfectly flat color image (no texture) has no edges at all -
    # correctly caught by the blur heuristic, which is exactly what it's
    # meant to catch (out-of-focus or featureless photos), never a
    # disease judgment.
    validated = validate_upload(
        content=make_test_jpeg(color=(128, 128, 128), textured=False), declared_mime_type="image/jpeg", settings=settings
    )
    result = check_quality(validated.image, settings)
    assert "too_blurry" in result.reasons


def test_quality_never_mentions_disease_or_agricultural_terms():
    validated = validate_upload(content=make_test_jpeg(color=(2, 2, 2)), declared_mime_type="image/jpeg", settings=settings)
    result = check_quality(validated.image, settings)
    forbidden_terms = ["disease", "pest", "blight", "infection", "fungus", "healthy", "unhealthy"]
    joined = " ".join(result.reasons).lower()
    for term in forbidden_terms:
        assert term not in joined


def test_process_image_strips_exif_and_normalizes():
    validated = validate_upload(content=make_test_jpeg(), declared_mime_type="image/jpeg", settings=settings)
    processed = process_image(validated.image, settings=settings)
    assert processed.width > 0 and processed.height > 0
    assert len(processed.thumbnail_content) < len(processed.content)

    # Re-open the processed bytes and confirm no EXIF block survived.
    from io import BytesIO

    from PIL import Image

    reopened = Image.open(BytesIO(processed.content))
    exif = reopened.getexif()
    assert len(exif) == 0


def test_process_image_resizes_oversized_image_down_to_max_dimension():
    large_content = make_test_jpeg(width=3000, height=2000)
    validated = validate_upload(content=large_content, declared_mime_type="image/jpeg", settings=settings)
    processed = process_image(validated.image, settings=settings)
    assert max(processed.width, processed.height) <= settings.photo_max_dimension_px


def test_process_image_thumbnail_within_configured_bounds():
    validated = validate_upload(content=make_test_jpeg(width=2000, height=1000), declared_mime_type="image/jpeg", settings=settings)
    processed = process_image(validated.image, settings=settings)
    assert max(processed.thumbnail_width, processed.thumbnail_height) <= settings.photo_thumbnail_max_dimension_px

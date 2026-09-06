"""
Storage-key helpers for crop photos.

Note: LocalFileStorage.save() generates the final unique key itself
(container + a fresh UUID + sanitized filename) and returns it - callers
must persist THAT returned value, not a key they pre-compute themselves.
This module only builds the two inputs `save()` needs: a hierarchical
container path (farmer_id/crop_cycle_id) and a plain leaf filename.
"""
import uuid


def build_photo_container(*, farmer_id: uuid.UUID, crop_cycle_id: uuid.UUID) -> str:
    return f"crop-photos/{farmer_id}/{crop_cycle_id}"


def build_product_photo_container(*, product_id: uuid.UUID) -> str:
    """D26-02 (docs/audit/FINAL_CANONICAL_group_A.md): admin-uploaded
    product catalog images - not farmer-owned, so no farmer_id in the
    path, unlike build_photo_container above."""
    return f"product-photos/{product_id}"


def build_leaf_filename(*, extension: str) -> str:
    return f"{uuid.uuid4().hex}.{_sanitize_extension(extension)}"


def _sanitize_extension(extension: str) -> str:
    cleaned = "".join(c for c in extension.lower() if c.isalnum())
    return cleaned or "jpg"

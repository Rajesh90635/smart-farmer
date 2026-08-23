"""
Zero-cost local-disk storage for the free/local MVP tier.
"""
import os
import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.logging_config import get_logger
from app.services.storage.base import FileStorage

logger = get_logger(__name__)


class LocalFileStorage(FileStorage):
    def __init__(self, root_path: str):
        self._root = Path(root_path).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, container: str, file_name: str, content: BinaryIO, content_type: str) -> str:
        safe_container = self._sanitize_container(container)
        safe_name = self._sanitize_segment(file_name)
        storage_key = f"{safe_container}/{uuid.uuid4().hex}-{safe_name}"

        full_path = self._resolve(storage_key)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(content.read())

        logger.info("Stored file", extra={"storage_key": storage_key, "content_type": content_type})
        return storage_key

    def open_read(self, storage_key: str) -> BinaryIO:
        full_path = self._resolve(storage_key)
        if not full_path.exists():
            raise FileNotFoundError(storage_key)
        return open(full_path, "rb")

    def delete(self, storage_key: str) -> None:
        full_path = self._resolve(storage_key)
        if full_path.exists():
            os.remove(full_path)

    def exists(self, storage_key: str) -> bool:
        return self._resolve(storage_key).exists()

    def _resolve(self, storage_key: str) -> Path:
        """Rejects any key that would resolve outside the storage root
        (path traversal defense) — required here because this class sits
        directly behind the future public image-upload endpoint."""
        candidate = (self._root / storage_key).resolve()
        if self._root not in candidate.parents and candidate != self._root:
            raise ValueError("Invalid storage key: path traversal detected.")
        return candidate

    @staticmethod
    def _sanitize_segment(segment: str) -> str:
        cleaned = "".join(c for c in segment if c.isalnum() or c in ("-", "_", "."))
        return cleaned or "unnamed"

    @classmethod
    def _sanitize_container(cls, container: str) -> str:
        """
        Extension (crop-photo module): supports a hierarchical container
        like "crop-photos/{farmer_id}/{crop_cycle_id}" in addition to the
        original flat single-segment form ("crop-images"), because the
        crop-photo module needs farmer/crop-cycle-scoped physical grouping
        on disk. Each "/"-delimited segment is sanitized independently and
        empty/".."-only segments are rejected - this is safe specifically
        because `container` is always a server-constructed value (UUIDs
        from the authenticated session and validated resource chain), never
        raw client input. Existing single-segment callers are unaffected:
        a container with no "/" behaves exactly as before.
        """
        segments = [cls._sanitize_segment(part) for part in container.split("/") if part not in ("", ".", "..")]
        return "/".join(segments) if segments else "unnamed"

"""
FastAPI dependency providing the configured FileStorage implementation.
Business code depends on this function (and the FileStorage interface),
never on LocalFileStorage directly - swapping storage backends later means
changing this one function.
"""
from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.base import FileStorage
from app.services.storage.local_storage import LocalFileStorage


@lru_cache
def get_file_storage() -> FileStorage:
    settings = get_settings()
    return LocalFileStorage(root_path=settings.local_storage_root)

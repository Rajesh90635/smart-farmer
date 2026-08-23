"""
File storage abstraction. Business modules (crop image upload, voice
message storage, documents) depend on this interface, never on "the
filesystem" directly — so LocalFileStorage can be swapped for an
Azure Blob / S3-compatible implementation later with zero change to
calling code.
"""
from abc import ABC, abstractmethod
from typing import BinaryIO


class FileStorage(ABC):
    @abstractmethod
    def save(self, container: str, file_name: str, content: BinaryIO, content_type: str) -> str:
        """Stores content and returns a storage_key to persist on the owning record."""

    @abstractmethod
    def open_read(self, storage_key: str) -> BinaryIO:
        ...

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        ...

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        ...

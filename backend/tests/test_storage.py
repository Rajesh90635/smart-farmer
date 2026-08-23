import io
import shutil
import tempfile

import pytest

from app.services.storage.local_storage import LocalFileStorage


@pytest.fixture()
def storage():
    tmp_dir = tempfile.mkdtemp()
    yield LocalFileStorage(root_path=tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_save_and_read_round_trip(storage):
    content = io.BytesIO(b"fake image bytes")
    key = storage.save("crop-images", "leaf.jpg", content, "image/jpeg")

    assert storage.exists(key)
    with storage.open_read(key) as f:
        assert f.read() == b"fake image bytes"


def test_delete_removes_file(storage):
    content = io.BytesIO(b"data")
    key = storage.save("crop-images", "leaf.jpg", content, "image/jpeg")
    storage.delete(key)
    assert not storage.exists(key)


def test_path_traversal_is_rejected(storage):
    with pytest.raises(ValueError):
        storage.open_read("../../etc/passwd")


def test_open_read_missing_file_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.open_read("crop-images/does-not-exist.jpg")

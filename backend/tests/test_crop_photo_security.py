import io

from tests.conftest import auth_headers
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload


def _create_session_and_upload(client, tokens, crop_cycle_id):
    session = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    ).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": "sec-test-1", "source": "camera"}
    photo = client.post(
        f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)
    ).json()
    return session, photo


def test_unauthenticated_upload_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id))
    assert response.status_code == 401


def test_farmer_a_cannot_upload_against_farmer_bs_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer

    # Farmer B tries to create a session directly against Farmer A's crop cycle.
    response = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_farmer_a_cannot_view_farmer_bs_photo(client, farmer_with_crop_cycle, another_farmer):
    tokens_a, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    _, photo = _create_session_and_upload(client, tokens_a, crop_cycle_id)

    response = client.get(f"/api/v1/crop-photos/{photo['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404

    file_response = client.get(f"/api/v1/crop-photos/{photo['id']}/file", headers=auth_headers(tokens_b))
    assert file_response.status_code == 404


def test_farmer_a_cannot_delete_farmer_bs_photo(client, farmer_with_crop_cycle, another_farmer):
    tokens_a, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    _, photo = _create_session_and_upload(client, tokens_a, crop_cycle_id)

    response = client.delete(f"/api/v1/crop-photos/{photo['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404

    # Farmer A's photo must be untouched.
    still_there = client.get(f"/api/v1/crop-photos/{photo['id']}", headers=auth_headers(tokens_a))
    assert still_there.status_code == 200


def test_farmer_a_cannot_upload_into_farmer_bs_session(client, farmer_with_crop_cycle, another_farmer):
    tokens_a, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    session, _ = _create_session_and_upload(client, tokens_a, crop_cycle_id)

    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": "hijack-attempt", "source": "camera"}
    response = client.post(
        f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_malicious_filename_does_not_affect_storage_path(client, farmer_with_crop_cycle):
    """A hostile client-supplied filename must never be usable as (or
    become part of) the storage path - storage keys are always
    server-generated UUIDs (see app/core/photo_storage_keys.py)."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    ).json()

    malicious_filename = "../../../etc/passwd.jpg"
    files = {"file": (malicious_filename, io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": "malicious-name-1", "source": "camera"}
    response = client.post(
        f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    body = response.json()
    # The sanitized filename is safe to display; it must not contain path
    # separators that could be (mis)used if ever rendered into a path.
    assert "/" not in body["original_filename"]
    assert ".." not in body["original_filename"]


def test_storage_layer_rejects_path_traversal_in_storage_key(tmp_path):
    """Direct unit test of the underlying LocalFileStorage - the crop
    photo module reuses this existing, already-tested defense rather than
    reimplementing its own."""
    from app.services.storage.local_storage import LocalFileStorage

    storage = LocalFileStorage(root_path=str(tmp_path))
    import pytest

    with pytest.raises(ValueError):
        storage.open_read("../../etc/passwd")


def test_unauthorized_storage_access_via_unowned_photo_id_is_rejected(client, farmer_with_crop_cycle, another_farmer):
    """Even knowing a valid (but not-owned) photo id, Farmer B cannot
    retrieve the file bytes - the ownership check happens before storage
    is ever touched."""
    tokens_a, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    _, photo = _create_session_and_upload(client, tokens_a, crop_cycle_id)

    response = client.get(f"/api/v1/crop-photos/{photo['id']}/file?thumbnail=true", headers=auth_headers(tokens_b))
    assert response.status_code == 404

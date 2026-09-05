import io

from tests.conftest import auth_headers
from tests.photo_factories import make_test_jpeg, make_test_png, valid_photo_session_payload


def _create_session(client, tokens, crop_cycle_id):
    return client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    ).json()


def _upload(client, tokens, session_id, *, content, mime_type="image/jpeg", filename="leaf.jpg",
            client_upload_id="upload-1", source="camera", **extra_fields):
    files = {"file": (filename, io.BytesIO(content), mime_type)}
    data = {"client_upload_id": client_upload_id, "source": source, **extra_fields}
    return client.post(
        f"/api/v1/crop-photo-sessions/{session_id}/photos",
        files=files,
        data=data,
        headers=auth_headers(tokens),
    )


def test_create_photo_session(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    assert response.json()["crop_cycle_id"] == crop_cycle_id


def test_cannot_create_session_for_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer

    response = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_upload_valid_photo(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"], content=make_test_jpeg())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["upload_status"] == "ready"
    assert body["image_quality_status"] == "accepted"
    assert body["mime_type"] == "image/jpeg"
    assert body["width_px"] > 0 and body["height_px"] > 0
    assert body["crop_cycle_id"] == crop_cycle_id


def test_upload_png_is_accepted_and_normalized_to_jpeg_storage(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"], content=make_test_png(), mime_type="image/png", filename="leaf.png")
    assert response.status_code == 201, response.text
    # Stored/served as JPEG regardless of input format - see crop_photo_service.py.
    assert response.json()["mime_type"] == "image/jpeg"


def test_upload_dark_photo_is_accepted_but_flagged_low_quality(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    dark_content = make_test_jpeg(color=(2, 2, 2))
    response = _upload(client, tokens, session["id"], content=dark_content)
    assert response.status_code == 201
    body = response.json()
    assert body["upload_status"] == "ready"  # the upload itself succeeded
    assert body["image_quality_status"] == "rejected"
    assert "too_dark" in body["quality_reasons"]


def test_upload_too_small_image_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"], content=make_test_jpeg(width=50, height=50))
    assert response.status_code == 422


def test_upload_corrupted_file_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"], content=b"not a real image, just bytes")
    assert response.status_code == 422


def test_upload_unsupported_mime_type_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"], content=make_test_jpeg(), mime_type="application/pdf")
    assert response.status_code == 422


def test_upload_oversized_file_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    # Larger than the configured 10MB limit, still declared as JPEG.
    oversized = b"\xff\xd8\xff" + (b"\x00" * (10 * 1024 * 1024 + 1))
    response = _upload(client, tokens, session["id"], content=oversized)
    assert response.status_code == 422


def test_retry_with_same_client_upload_id_does_not_duplicate(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    first = _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="same-id")
    assert first.status_code == 201
    first_photo_id = first.json()["id"]

    # Simulated retry after a "network failure" - same client_upload_id.
    second = _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="same-id")
    assert second.status_code == 201
    assert second.json()["id"] == first_photo_id

    listing = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/photos", headers=auth_headers(tokens))
    assert listing.json()["total"] == 1


def test_different_client_upload_ids_create_separate_photos(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="upload-a")
    _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="upload-b")

    listing = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/photos", headers=auth_headers(tokens))
    assert listing.json()["total"] == 2


def test_multiple_photos_per_session_supported(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    for i, label in enumerate(["whole-plant", "affected-leaf", "close-up", "stem"]):
        _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id=f"photo-{label}-{i}")

    listing = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/photos", headers=auth_headers(tokens))
    assert listing.json()["total"] == 4


def test_location_only_recorded_with_explicit_consent(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    without_consent = _upload(
        client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="no-consent",
        latitude="10.5", longitude="76.2",  # provided but share_location NOT set
    )
    assert without_consent.json()["latitude"] is None

    with_consent = _upload(
        client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="with-consent",
        share_location="true", latitude="10.5", longitude="76.2",
    )
    assert with_consent.json()["latitude"] == "10.500000"


def test_get_photo_detail(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)
    uploaded = _upload(client, tokens, session["id"], content=make_test_jpeg()).json()

    response = client.get(f"/api/v1/crop-photos/{uploaded['id']}", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["id"] == uploaded["id"]


def test_get_photo_file_returns_image_bytes(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)
    uploaded = _upload(client, tokens, session["id"], content=make_test_jpeg()).json()

    response = client.get(f"/api/v1/crop-photos/{uploaded['id']}/file", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_get_thumbnail_file(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)
    uploaded = _upload(client, tokens, session["id"], content=make_test_jpeg()).json()

    full = client.get(f"/api/v1/crop-photos/{uploaded['id']}/file", headers=auth_headers(tokens))
    thumb = client.get(f"/api/v1/crop-photos/{uploaded['id']}/file?thumbnail=true", headers=auth_headers(tokens))
    assert thumb.status_code == 200
    assert len(thumb.content) < len(full.content)  # thumbnail must actually be smaller


def test_delete_photo_is_soft_delete(client, farmer_with_crop_cycle, db_session):
    import uuid as uuid_mod

    from app.models.crop_photo import CropPhoto, UploadStatus

    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)
    uploaded = _upload(client, tokens, session["id"], content=make_test_jpeg()).json()

    delete_response = client.delete(f"/api/v1/crop-photos/{uploaded['id']}", headers=auth_headers(tokens))
    assert delete_response.status_code == 204

    # Excluded from normal retrieval...
    get_response = client.get(f"/api/v1/crop-photos/{uploaded['id']}", headers=auth_headers(tokens))
    assert get_response.status_code == 404

    # ...but the row and its files still exist (soft delete, not physical).
    row = db_session.get(CropPhoto, uuid_mod.UUID(uploaded["id"]))
    assert row is not None
    assert row.upload_status == UploadStatus.DELETED


def test_upload_is_rate_limited_per_farmer(client, farmer_with_crop_cycle):
    """D100-14 (docs/audit/c13_governance_farmbrain_security.md):
    rate_limit.py's own docstring named image-upload endpoints as an
    intended target from the start, but nothing was ever wired in -
    confirmed by grep before this fix."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    for i in range(20):
        response = _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id=f"rate-limit-{i}")
        assert response.status_code == 201, response.text

    over_limit = _upload(client, tokens, session["id"], content=make_test_jpeg(), client_upload_id="rate-limit-21")
    assert over_limit.status_code == 429


def test_upload_rate_limit_is_scoped_per_farmer_not_global(client, farmer_with_crop_cycle, another_farmer, sample_crop_id):
    """A different farmer's uploads must never be blocked by another
    farmer's usage - the limiter is keyed by farmer_id, not shared."""
    tokens_a, crop_cycle_id_a = farmer_with_crop_cycle
    session_a = _create_session(client, tokens_a, crop_cycle_id_a)
    for i in range(20):
        _upload(client, tokens_a, session_a["id"], content=make_test_jpeg(), client_upload_id=f"farmer-a-{i}")

    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    _, tokens_b = another_farmer
    headers_b = auth_headers(tokens_b)
    farm_b = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers_b).json()
    plot_b = client.post(f"/api/v1/farms/{farm_b['id']}/plots", json=valid_plot_payload(), headers=headers_b).json()
    cycle_b = client.post(f"/api/v1/plots/{plot_b['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers_b).json()
    session_b = _create_session(client, tokens_b, cycle_b["id"])

    response = _upload(client, tokens_b, session_b["id"], content=make_test_jpeg(), client_upload_id="farmer-b-1")
    assert response.status_code == 201

"""
Missing Backlog Batch 8 (group 5): D74-03 (docs/audit/FINAL_CANONICAL_group_D.md).
"""
import io

from tests.conftest import auth_headers
from tests.photo_factories import make_test_jpeg


def _create_damage_record(client, tokens, crop_cycle_id):
    policy = client.post(
        "/api/v1/farmers/me/insurance-policies",
        json={"policy_number": "POL-1", "insurer": "Test Insurer", "sum_insured": "50000.00", "premium": "1000.00"},
        headers=auth_headers(tokens),
    ).json()
    return client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/damage-records",
        json={"policy_id": policy["id"], "loss_type": "flood", "extent_percent": "40.00", "occurred_on": "2026-08-01"},
        headers=auth_headers(tokens),
    ).json()


def _create_session(client, tokens, crop_cycle_id):
    return client.post(
        "/api/v1/crop-photo-sessions", json={"crop_cycle_id": crop_cycle_id}, headers=auth_headers(tokens)
    ).json()


def _upload(client, tokens, session_id, **extra_fields):
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": "upload-1", "source": "camera", **extra_fields}
    return client.post(
        f"/api/v1/crop-photo-sessions/{session_id}/photos", files=files, data=data, headers=auth_headers(tokens)
    )


def test_photo_uploaded_without_damage_record_id_has_none(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"])
    assert response.status_code == 201
    assert response.json()["damage_record_id"] is None


def test_photo_can_be_linked_to_an_owned_damage_record(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    damage_record = _create_damage_record(client, tokens, crop_cycle_id)
    session = _create_session(client, tokens, crop_cycle_id)

    response = _upload(client, tokens, session["id"], damage_record_id=damage_record["id"])
    assert response.status_code == 201
    assert response.json()["damage_record_id"] == damage_record["id"]


def test_photo_upload_rejects_a_damage_record_from_another_crop_cycle(client, registered_farmer, sample_crop_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    _, tokens = registered_farmer
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()

    plot_a = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_a = client.post(
        f"/api/v1/plots/{plot_a['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    ).json()
    damage_record_a = _create_damage_record(client, tokens, cycle_a["id"])

    plot_b = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(plot_name="Other Plot"), headers=headers
    ).json()
    cycle_b = client.post(
        f"/api/v1/plots/{plot_b['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers
    ).json()
    session_b = _create_session(client, tokens, cycle_b["id"])

    response = _upload(client, tokens, session_b["id"], damage_record_id=damage_record_a["id"])
    assert response.status_code == 404


def test_photo_upload_rejects_another_farmers_damage_record(client, farmer_with_crop_cycle, another_farmer, sample_crop_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    damage_record = _create_damage_record(client, tokens, crop_cycle_id)

    _, other_tokens = another_farmer
    other_headers = auth_headers(other_tokens)
    other_farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=other_headers).json()
    other_plot = client.post(
        f"/api/v1/farms/{other_farm['id']}/plots", json=valid_plot_payload(), headers=other_headers
    ).json()
    other_cycle = client.post(
        f"/api/v1/plots/{other_plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=other_headers
    ).json()
    other_session = _create_session(client, other_tokens, other_cycle["id"])

    response = _upload(client, other_tokens, other_session["id"], damage_record_id=damage_record["id"])
    assert response.status_code == 404
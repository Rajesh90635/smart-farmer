"""
D18-06 (docs/audit/FINAL_CANONICAL_group_A.md): irrigation activity
records - mirrors test_treatments.py's shape for the irrigation domain.
"""
from tests.conftest import auth_headers


def test_create_irrigation_record(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-01", "duration_minutes": "45", "volume_liters": "500", "source": "drip"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["crop_cycle_id"] == crop_cycle_id
    assert body["duration_minutes"] == "45.00"
    assert body["source"] == "drip"
    assert body["failure_note"] is None


def test_irrigation_record_can_flag_a_pump_failure(client, farmer_with_crop_cycle):
    """D18-08 (docs/audit/FINAL_CANONICAL_group_A.md)."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-01", "failure_note": "Pump motor stopped mid-cycle"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    assert response.json()["failure_note"] == "Pump motor stopped mid-cycle"


def test_irrigation_record_can_link_to_a_task(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks", json={"title": "Irrigate", "task_type": "irrigation"}, headers=auth_headers(tokens)
    ).json()

    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-01", "task_id": task["id"]},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    assert response.json()["task_id"] == task["id"]


def test_irrigation_record_task_must_belong_to_the_same_crop_cycle(client, farmer_with_crop_cycle, sample_crop_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    other_cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    other_task = client.post(
        f"/api/v1/crop-cycles/{other_cycle['id']}/tasks", json={"title": "Irrigate"}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-01", "task_id": other_task["id"]},
        headers=headers,
    )
    assert response.status_code == 422


def test_list_irrigation_records_for_crop_cycle(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-01"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-05"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_cannot_create_irrigation_record_under_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-records",
        json={"irrigation_date": "2026-06-01"},
        headers=auth_headers(tokens_b),
    )
    assert response.status_code == 404

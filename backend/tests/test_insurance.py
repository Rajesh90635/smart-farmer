from tests.conftest import auth_headers


def _valid_policy_payload(**overrides):
    payload = {
        "policy_number": "PMFBY-2026-00123",
        "insurer": "Agriculture Insurance Company",
        "sum_insured": "50000.00",
        "premium": "1200.00",
        "season": "kharif_2026",
    }
    payload.update(overrides)
    return payload


def test_farmer_can_create_and_view_an_insurance_policy(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post("/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(), headers=auth_headers(tokens))
    assert created.status_code == 201
    body = created.json()
    assert body["policy_number"] == "PMFBY-2026-00123"
    assert body["crop_id"] is None

    fetched = client.get(f"/api/v1/farmers/me/insurance-policies/{body['id']}", headers=auth_headers(tokens))
    assert fetched.status_code == 200
    assert fetched.json()["insurer"] == "Agriculture Insurance Company"


def test_farmer_can_create_a_policy_linked_to_a_real_crop(client, registered_farmer, sample_crop_id):
    _, tokens = registered_farmer
    created = client.post(
        "/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(crop_id=sample_crop_id), headers=auth_headers(tokens)
    )
    assert created.status_code == 201
    assert created.json()["crop_id"] == sample_crop_id


def test_creating_a_policy_with_a_nonexistent_crop_is_rejected(client, registered_farmer):
    import uuid

    _, tokens = registered_farmer
    response = client.post(
        "/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(crop_id=str(uuid.uuid4())), headers=auth_headers(tokens)
    )
    assert response.status_code == 422


def test_list_returns_only_the_farmers_own_policies(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    _, other_tokens = another_farmer

    client.post("/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(), headers=auth_headers(tokens))
    client.post("/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(policy_number="OTHER-001"), headers=auth_headers(other_tokens))

    listed = client.get("/api/v1/farmers/me/insurance-policies", headers=auth_headers(tokens)).json()
    assert listed["total"] == 1
    assert listed["items"][0]["policy_number"] == "PMFBY-2026-00123"


def test_a_farmer_cannot_view_another_farmers_policy(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    _, other_tokens = another_farmer

    created = client.post("/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(), headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/farmers/me/insurance-policies/{created['id']}", headers=auth_headers(other_tokens))
    assert response.status_code == 404


def test_a_farmer_cannot_delete_another_farmers_policy(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    _, other_tokens = another_farmer

    created = client.post("/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(), headers=auth_headers(tokens)).json()

    response = client.delete(f"/api/v1/farmers/me/insurance-policies/{created['id']}", headers=auth_headers(other_tokens))
    assert response.status_code == 404


def test_farmer_can_delete_their_own_policy(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post("/api/v1/farmers/me/insurance-policies", json=_valid_policy_payload(), headers=auth_headers(tokens)).json()

    response = client.delete(f"/api/v1/farmers/me/insurance-policies/{created['id']}", headers=auth_headers(tokens))
    assert response.status_code == 204

    fetched = client.get(f"/api/v1/farmers/me/insurance-policies/{created['id']}", headers=auth_headers(tokens))
    assert fetched.status_code == 404

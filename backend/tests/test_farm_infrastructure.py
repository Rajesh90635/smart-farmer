"""D2-07 (docs/audit/FINAL_CANONICAL_group_A.md): farmer-entered farm
infrastructure records, informational only."""
from tests.conftest import auth_headers
from tests.farm_factories import valid_farm_payload


def _create_farm(client, tokens):
    return client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()


def test_farmer_can_create_and_list_farm_infrastructure(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)

    created = client.post(
        f"/api/v1/farms/{farm['id']}/infrastructure",
        json={"infrastructure_type": "well", "description": "Hand-dug well near the north field"},
        headers=auth_headers(tokens),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["infrastructure_type"] == "well"
    assert body["description"] == "Hand-dug well near the north field"
    assert body["farm_id"] == farm["id"]

    listed = client.get(f"/api/v1/farms/{farm['id']}/infrastructure", headers=auth_headers(tokens)).json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == body["id"]


def test_farm_infrastructure_description_is_optional(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)

    response = client.post(
        f"/api/v1/farms/{farm['id']}/infrastructure", json={"infrastructure_type": "storage"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_farmer_can_delete_their_own_infrastructure_record(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    created = client.post(
        f"/api/v1/farms/{farm['id']}/infrastructure", json={"infrastructure_type": "shed"}, headers=auth_headers(tokens)
    ).json()

    response = client.delete(f"/api/v1/farms/{farm['id']}/infrastructure/{created['id']}", headers=auth_headers(tokens))
    assert response.status_code == 204

    listed = client.get(f"/api/v1/farms/{farm['id']}/infrastructure", headers=auth_headers(tokens)).json()
    assert listed["total"] == 0


def test_cannot_create_infrastructure_under_another_farmers_farm(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    _, other_tokens = another_farmer

    response = client.post(
        f"/api/v1/farms/{farm['id']}/infrastructure", json={"infrastructure_type": "well"}, headers=auth_headers(other_tokens)
    )
    assert response.status_code == 404


def test_cannot_list_infrastructure_for_another_farmers_farm(client, registered_farmer, another_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    _, other_tokens = another_farmer

    response = client.get(f"/api/v1/farms/{farm['id']}/infrastructure", headers=auth_headers(other_tokens))
    assert response.status_code == 404

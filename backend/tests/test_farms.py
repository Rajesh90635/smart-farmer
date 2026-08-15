from tests.conftest import auth_headers
from tests.farm_factories import valid_farm_payload


def test_create_farm(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["farm_name"] == "Test Farm"
    # Postgres NUMERIC(12,4) correctly returns the full declared scale
    # ("2.5000"), not the originally-submitted string ("2.5") - compare
    # numerically, not as strings, since this is expected DB behavior.
    assert float(body["area_value"]) == 2.5
    assert body["status"] == "active"


def test_list_my_farms(client, registered_farmer):
    _, tokens = registered_farmer
    client.post("/api/v1/farms", json=valid_farm_payload(farm_name="Farm A"), headers=auth_headers(tokens))
    client.post("/api/v1/farms", json=valid_farm_payload(farm_name="Farm B"), headers=auth_headers(tokens))

    response = client.get("/api/v1/farms", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    names = {f["farm_name"] for f in body["items"]}
    assert names == {"Farm A", "Farm B"}


def test_get_own_farm(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/farms/{created['id']}", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_own_farm(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()

    response = client.put(
        f"/api/v1/farms/{created['id']}", json={"farm_name": "Renamed Farm"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["farm_name"] == "Renamed Farm"


def test_update_area_recomputes_canonical_value_consistently(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post(
        "/api/v1/farms", json=valid_farm_payload(area_value="1", area_unit="acre"), headers=auth_headers(tokens)
    ).json()

    # Change only the unit - area_value should be reinterpreted under the
    # new unit consistently, not silently left mismatched.
    response = client.put(
        f"/api/v1/farms/{created['id']}", json={"area_unit": "hectare"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["area_unit"] == "hectare"


def test_deactivate_farm_removes_it_from_active_list(client, registered_farmer):
    _, tokens = registered_farmer
    created = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()

    deactivate_response = client.delete(f"/api/v1/farms/{created['id']}", headers=auth_headers(tokens))
    assert deactivate_response.status_code == 204

    list_response = client.get("/api/v1/farms", headers=auth_headers(tokens))
    assert list_response.json()["total"] == 0


def test_invalid_area_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post(
        "/api/v1/farms", json=valid_farm_payload(area_value="-5"), headers=auth_headers(tokens)
    )
    assert response.status_code == 422


def test_invalid_latitude_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post(
        "/api/v1/farms", json=valid_farm_payload(latitude="200"), headers=auth_headers(tokens)
    )
    assert response.status_code == 422


def test_unauthorized_farm_access_is_rejected(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer

    farm_a = client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens_a)).json()

    # Farmer B must not be able to read, update, or deactivate Farmer A's farm.
    get_resp = client.get(f"/api/v1/farms/{farm_a['id']}", headers=auth_headers(tokens_b))
    assert get_resp.status_code == 404  # not 403 - see farm_service.get_my_farm's ID-enumeration reasoning

    put_resp = client.put(
        f"/api/v1/farms/{farm_a['id']}", json={"farm_name": "Hijacked"}, headers=auth_headers(tokens_b)
    )
    assert put_resp.status_code == 404

    delete_resp = client.delete(f"/api/v1/farms/{farm_a['id']}", headers=auth_headers(tokens_b))
    assert delete_resp.status_code == 404

    # Farmer A's farm must be untouched.
    still_there = client.get(f"/api/v1/farms/{farm_a['id']}", headers=auth_headers(tokens_a))
    assert still_there.json()["farm_name"] == "Test Farm"

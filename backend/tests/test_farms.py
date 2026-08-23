import uuid

from app.models.location import Mandal, Village
from tests.conftest import auth_headers
from tests.farm_factories import valid_farm_payload


def _ap_state_id(client, tokens) -> int:
    states = client.get("/api/v1/states", headers=auth_headers(tokens)).json()
    return next(s["id"] for s in states if s["code"] == "AP")


def _guntur_district_id(client, tokens) -> int:
    ap_id = _ap_state_id(client, tokens)
    districts = client.get(f"/api/v1/states/{ap_id}/districts", headers=auth_headers(tokens)).json()
    return next(d["id"] for d in districts if d["name"] == "Guntur")


def _make_mandal_and_village(db_session, district_id: int):
    # Real Postgres DB, not rolled back between tests - names must be
    # unique per test run (same convention as tests/factories.py's
    # unique_phone()), since (district_id, name) is a real DB constraint.
    suffix = uuid.uuid4().hex[:8]
    mandal_name = f"Tenali {suffix}"
    village_name = f"Angalakuduru {suffix}"
    mandal = Mandal(district_id=district_id, name=mandal_name)
    db_session.add(mandal)
    db_session.commit()
    db_session.refresh(mandal)
    village = Village(mandal_id=mandal.id, name=village_name)
    db_session.add(village)
    db_session.commit()
    db_session.refresh(village)
    return mandal.id, mandal_name, village.id, village_name


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


def test_create_farm_with_full_location_chain_returns_ids_and_names(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    state_id = _ap_state_id(client, tokens)
    district_id = _guntur_district_id(client, tokens)
    mandal_id, mandal_name, village_id, village_name = _make_mandal_and_village(db_session, district_id)

    response = client.post(
        "/api/v1/farms",
        json=valid_farm_payload(
            state_id=state_id, district_id=district_id, mandal_id=mandal_id, village_id=village_id
        ),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["state_id"] == state_id
    assert body["district_id"] == district_id
    assert body["mandal_id"] == mandal_id
    assert body["village_id"] == village_id
    assert body["state_name"] == "Andhra Pradesh"
    assert body["district_name"] == "Guntur"
    assert body["mandal_name"] == mandal_name
    assert body["village_name"] == village_name


def test_create_farm_with_only_state_and_district_leaves_mandal_village_null(client, registered_farmer):
    _, tokens = registered_farmer
    state_id = _ap_state_id(client, tokens)
    district_id = _guntur_district_id(client, tokens)

    response = client.post(
        "/api/v1/farms",
        json=valid_farm_payload(state_id=state_id, district_id=district_id),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["district_id"] == district_id
    assert body["mandal_id"] is None
    assert body["village_name"] is None


def test_create_farm_rejects_district_not_belonging_to_given_state(client, registered_farmer, db_session):
    from sqlalchemy import select

    from app.models.location import District, State

    _, tokens = registered_farmer
    state_id = _ap_state_id(client, tokens)

    # Real Postgres DB, not rolled back between tests - get-or-create so
    # re-running the suite doesn't collide on State.code's unique
    # constraint (unlike farmer-scoped data, a second "Karnataka" row
    # would be genuinely wrong reference data, not just a test collision).
    other_state = db_session.execute(select(State).where(State.code == "KA")).scalar_one_or_none()
    if other_state is None:
        other_state = State(code="KA", name="Karnataka")
        db_session.add(other_state)
        db_session.commit()
        db_session.refresh(other_state)
    other_district = db_session.execute(
        select(District).where(District.state_id == other_state.id, District.name == "Bengaluru Urban")
    ).scalar_one_or_none()
    if other_district is None:
        other_district = District(state_id=other_state.id, name="Bengaluru Urban")
        db_session.add(other_district)
        db_session.commit()
        db_session.refresh(other_district)

    response = client.post(
        "/api/v1/farms",
        json=valid_farm_payload(state_id=state_id, district_id=other_district.id),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_farm_rejects_unknown_district_id(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.post(
        "/api/v1/farms",
        json=valid_farm_payload(district_id=999999),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_farm_location_validates_against_existing_stored_chain(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    state_id = _ap_state_id(client, tokens)
    district_id = _guntur_district_id(client, tokens)
    created = client.post(
        "/api/v1/farms",
        json=valid_farm_payload(state_id=state_id, district_id=district_id),
        headers=auth_headers(tokens),
    ).json()

    mandal_id, _, _, _ = _make_mandal_and_village(db_session, district_id)
    response = client.put(
        f"/api/v1/farms/{created['id']}", json={"mandal_id": mandal_id}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mandal_id"] == mandal_id
    assert body["district_id"] == district_id  # untouched levels are preserved, not cleared
    assert body["state_id"] == state_id

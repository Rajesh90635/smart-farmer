import uuid

from app.models.location import Mandal, Village
from tests.conftest import auth_headers


def _make_mandal(db_session, district_id: int, name: str | None = None) -> tuple[int, str]:
    # Real Postgres DB, not rolled back between tests (same convention as
    # tests/factories.py's unique_phone()) - names must be unique per test
    # run since (district_id, name) is a real DB constraint.
    name = name or f"Test Mandal {uuid.uuid4().hex[:8]}"
    mandal = Mandal(district_id=district_id, name=name)
    db_session.add(mandal)
    db_session.commit()
    db_session.refresh(mandal)
    return mandal.id, name


def _make_village(db_session, mandal_id: int, name: str | None = None) -> tuple[int, str]:
    name = name or f"Test Village {uuid.uuid4().hex[:8]}"
    village = Village(mandal_id=mandal_id, name=name)
    db_session.add(village)
    db_session.commit()
    db_session.refresh(village)
    return village.id, name


def test_list_states_returns_seeded_andhra_pradesh(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/states", headers=auth_headers(tokens))
    assert response.status_code == 200
    states = response.json()
    ap = next((s for s in states if s["code"] == "AP"), None)
    assert ap is not None
    assert ap["name"] == "Andhra Pradesh"


def test_list_districts_for_a_state_returns_26_districts(client, registered_farmer):
    _, tokens = registered_farmer
    states = client.get("/api/v1/states", headers=auth_headers(tokens)).json()
    ap_id = next(s["id"] for s in states if s["code"] == "AP")

    response = client.get(f"/api/v1/states/{ap_id}/districts", headers=auth_headers(tokens))
    assert response.status_code == 200
    districts = response.json()
    assert len(districts) == 26
    names = {d["name"] for d in districts}
    assert "Visakhapatnam" in names
    assert "Chittoor" in names


def test_districts_for_an_unknown_state_returns_404(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/states/999999/districts", headers=auth_headers(tokens))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/api/v1/states")
    assert response.status_code == 401


def test_list_mandals_for_a_district_returns_the_mandal_just_created(client, registered_farmer, db_session):
    # Mandal has no seed data anywhere - a real mandal is inserted directly
    # via db_session (the same pattern test_ledger.py/test_crop_financials.py
    # use for data this project's own migrations don't seed), not fabricated
    # AP mandal names.
    _, tokens = registered_farmer
    states = client.get("/api/v1/states", headers=auth_headers(tokens)).json()
    ap_id = next(s["id"] for s in states if s["code"] == "AP")
    districts = client.get(f"/api/v1/states/{ap_id}/districts", headers=auth_headers(tokens)).json()
    district_id = next(d["id"] for d in districts if d["name"] == "Guntur")

    mandal_id, mandal_name = _make_mandal(db_session, district_id)

    response = client.get(f"/api/v1/districts/{district_id}/mandals", headers=auth_headers(tokens))
    assert response.status_code == 200
    mandals = response.json()
    assert {"id": mandal_id, "name": mandal_name} in mandals


def test_mandals_for_an_unknown_district_returns_404(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/districts/999999/mandals", headers=auth_headers(tokens))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_list_villages_for_a_mandal_returns_the_village_just_created(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    states = client.get("/api/v1/states", headers=auth_headers(tokens)).json()
    ap_id = next(s["id"] for s in states if s["code"] == "AP")
    districts = client.get(f"/api/v1/states/{ap_id}/districts", headers=auth_headers(tokens)).json()
    district_id = next(d["id"] for d in districts if d["name"] == "Guntur")
    mandal_id, _ = _make_mandal(db_session, district_id)

    village_id, village_name = _make_village(db_session, mandal_id)

    response = client.get(f"/api/v1/mandals/{mandal_id}/villages", headers=auth_headers(tokens))
    assert response.status_code == 200
    villages = response.json()
    assert {"id": village_id, "name": village_name} in villages


def test_villages_for_an_unknown_mandal_returns_404(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/mandals/999999/villages", headers=auth_headers(tokens))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

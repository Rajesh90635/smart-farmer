"""
Missing Backlog Batch 8 (group 7): D3-07 (docs/audit/FINAL_CANONICAL_group_A.md).
"""
from tests.conftest import auth_headers
from tests.farm_factories import valid_farm_payload, valid_plot_payload

_TRIANGLE = [
    {"latitude": "10.850000", "longitude": "76.271000"},
    {"latitude": "10.851000", "longitude": "76.272000"},
    {"latitude": "10.852000", "longitude": "76.271500"},
]


def _create_farm(client, tokens):
    return client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()


def test_plot_boundary_defaults_to_null(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()
    assert plot["boundary_points"] is None


def test_plot_boundary_can_be_set_at_creation(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json=valid_plot_payload(boundary_points=_TRIANGLE),
        headers=auth_headers(tokens),
    ).json()
    assert len(plot["boundary_points"]) == 3
    assert plot["boundary_points"][0]["latitude"] == "10.85"


def test_plot_boundary_with_fewer_than_3_points_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    resp = client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json=valid_plot_payload(boundary_points=_TRIANGLE[:2]),
        headers=auth_headers(tokens),
    )
    assert resp.status_code == 422


def test_plot_boundary_with_invalid_latitude_is_rejected(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    bad_points = _TRIANGLE[:2] + [{"latitude": "999.0", "longitude": "76.0"}]
    resp = client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json=valid_plot_payload(boundary_points=bad_points),
        headers=auth_headers(tokens),
    )
    assert resp.status_code == 422


def test_plot_boundary_can_be_updated(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()

    resp = client.put(f"/api/v1/plots/{plot['id']}", json={"boundary_points": _TRIANGLE}, headers=auth_headers(tokens))
    assert resp.status_code == 200
    assert len(resp.json()["boundary_points"]) == 3


def test_plot_boundary_does_not_affect_area_value(client, registered_farmer):
    """area_value/area_sqm are entirely separate, farmer-entered fields -
    the boundary is display/reference only, never used to (re)compute area."""
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json=valid_plot_payload(area_value="2.5", boundary_points=_TRIANGLE),
        headers=auth_headers(tokens),
    ).json()
    assert plot["area_value"] == "2.5000"

from tests.conftest import auth_headers
from tests.farm_factories import valid_farm_payload, valid_plot_payload


def _create_farm(client, tokens):
    return client.post("/api/v1/farms", json=valid_farm_payload(), headers=auth_headers(tokens)).json()


def test_create_plot(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)

    response = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["plot_name"] == "North Plot"
    assert body["farm_id"] == farm["id"]


def test_list_plots_for_farm(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(plot_name="Plot A"), headers=auth_headers(tokens))
    client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(plot_name="Plot B"), headers=auth_headers(tokens))

    response = client.get(f"/api/v1/farms/{farm['id']}/plots", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_plot(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()

    response = client.get(f"/api/v1/plots/{plot['id']}", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["id"] == plot["id"]


def test_update_plot(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()

    response = client.put(
        f"/api/v1/plots/{plot['id']}", json={"plot_name": "Renamed Plot"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["plot_name"] == "Renamed Plot"


def test_deactivate_plot(client, registered_farmer):
    _, tokens = registered_farmer
    farm = _create_farm(client, tokens)
    plot = client.post(
        f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens)
    ).json()

    deactivate = client.delete(f"/api/v1/plots/{plot['id']}", headers=auth_headers(tokens))
    assert deactivate.status_code == 204

    listing = client.get(f"/api/v1/farms/{farm['id']}/plots", headers=auth_headers(tokens))
    assert listing.json()["total"] == 0


def test_cannot_create_plot_under_another_farmers_farm(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer
    farm_a = _create_farm(client, tokens_a)

    response = client.post(
        f"/api/v1/farms/{farm_a['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_unauthorized_plot_access_is_rejected(client, registered_farmer, another_farmer):
    _, tokens_a = registered_farmer
    _, tokens_b = another_farmer
    farm_a = _create_farm(client, tokens_a)
    plot_a = client.post(
        f"/api/v1/farms/{farm_a['id']}/plots", json=valid_plot_payload(), headers=auth_headers(tokens_a)
    ).json()

    get_resp = client.get(f"/api/v1/plots/{plot_a['id']}", headers=auth_headers(tokens_b))
    assert get_resp.status_code == 404

    put_resp = client.put(
        f"/api/v1/plots/{plot_a['id']}", json={"plot_name": "Hijacked"}, headers=auth_headers(tokens_b)
    )
    assert put_resp.status_code == 404

    delete_resp = client.delete(f"/api/v1/plots/{plot_a['id']}", headers=auth_headers(tokens_b))
    assert delete_resp.status_code == 404

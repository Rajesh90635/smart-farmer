from tests.conftest import auth_headers
from tests.marketplace_factories import valid_dealer_listing_payload


def test_compare_offers_excludes_unverified_dealer(client, registered_farmer, verified_dealer, approved_product):
    _, farmer_tokens = registered_farmer
    tokens, _ = verified_dealer
    client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"], price="200.00"), headers=auth_headers(tokens))

    response = client.get(f"/api/v1/products/{approved_product['id']}/compare", headers=auth_headers(farmer_tokens))
    assert response.status_code == 200
    body = response.json()
    assert len(body["offers"]) == 1
    assert body["offers"][0]["dealer_price"] == "200.00"


def test_scam_shield_flags_a_high_price(client, registered_farmer, verified_dealer, approved_product, admin_tokens):
    _, farmer_tokens = registered_farmer
    tokens, _ = verified_dealer

    client.post(
        f"/api/v1/products/{approved_product['id']}/reference-prices",
        json={"product_id": approved_product["id"], "price": "250.00", "source_type": "admin_entered_reference", "effective_date": "2026-01-01"},
        headers=auth_headers(admin_tokens),
    )

    listing = client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"], price="400.00"), headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/dealer-products/{listing['id']}/scam-shield", headers=auth_headers(farmer_tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["anomaly_level"] is not None
    forbidden = ["scammer", "fraud", "cheater", "cheat"]
    assert not any(term in body["message"].lower() for term in forbidden)
    assert "reference price" in body["message"].lower()


def test_scam_shield_normal_price_no_flag(client, registered_farmer, verified_dealer, approved_product, admin_tokens):
    _, farmer_tokens = registered_farmer
    tokens, _ = verified_dealer

    client.post(
        f"/api/v1/products/{approved_product['id']}/reference-prices",
        json={"product_id": approved_product["id"], "price": "250.00", "source_type": "admin_entered_reference", "effective_date": "2026-01-01"},
        headers=auth_headers(admin_tokens),
    )
    listing = client.post("/api/v1/dealer-products", json=valid_dealer_listing_payload(approved_product["id"], price="255.00"), headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/dealer-products/{listing['id']}/scam-shield", headers=auth_headers(farmer_tokens))
    assert response.json()["anomaly_level"] is None


def test_reference_price_unavailable_returns_404(client, registered_farmer, admin_tokens):
    from tests.marketplace_factories import valid_product_payload

    product = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()
    client.post(f"/api/v1/products/{product['id']}/approve", json={}, headers=auth_headers(admin_tokens))

    _, farmer_tokens = registered_farmer
    response = client.get(f"/api/v1/products/{product['id']}/prices", headers=auth_headers(farmer_tokens))
    assert response.status_code == 404

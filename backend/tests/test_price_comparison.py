from decimal import Decimal

from tests.conftest import auth_headers
from tests.marketplace_factories import valid_dealer_listing_payload, valid_product_payload


def test_price_per_unit_never_returns_scientific_notation():
    """Regression test: plain Decimal division (price / pack_size_value)
    can return an exact-but-scientific-notation result for some inputs
    (e.g. Decimal("250.00") / Decimal("1.000") == Decimal("2.5E+2")) - the
    DB's own Numeric(10, 3) pack_size_value column reads back with exactly
    that 3-decimal-place shape, so this is a real, reachable case, not a
    contrived one. Serialized to JSON, "2.5E+2" would render as garbage in
    a farmer-facing price display. price_per_unit() must always quantize."""
    from app.services.price_comparison import price_per_unit

    result = price_per_unit(Decimal("250.00"), Decimal("1.000"))
    assert str(result) == "250.00"
    assert "E" not in str(result)

    result = price_per_unit(Decimal("100.00"), Decimal("1.000"))
    assert str(result) == "100.00"
    assert "E" not in str(result)


def test_compare_and_scam_shield_never_return_scientific_notation_price_fields(client, registered_farmer, verified_dealer, admin_tokens):
    """API-level regression for the same bug, covering both call sites -
    /compare's per-offer price_per_unit AND its separately-computed
    reference_price_per_unit (a real prior duplication that bypassed the
    fix in one of the two places), plus /scam-shield's own price_per_unit."""
    _, farmer_tokens = registered_farmer
    tokens, _ = verified_dealer

    product = client.post(
        "/api/v1/products", json=valid_product_payload(pack_size_value=1, pack_size_unit="litre"), headers=auth_headers(admin_tokens)
    ).json()
    client.post(f"/api/v1/products/{product['id']}/approve", json={}, headers=auth_headers(admin_tokens))
    client.post(
        f"/api/v1/products/{product['id']}/reference-prices",
        json={"product_id": product["id"], "price": "100.00", "source_type": "admin_entered_reference", "effective_date": "2026-01-01"},
        headers=auth_headers(admin_tokens),
    )
    listing = client.post(
        "/api/v1/dealer-products", json=valid_dealer_listing_payload(product["id"], price="250.00"), headers=auth_headers(tokens)
    ).json()

    compare = client.get(f"/api/v1/products/{product['id']}/compare", headers=auth_headers(farmer_tokens)).json()
    assert compare["reference_price_per_unit"] == "100.00"
    assert compare["offers"][0]["price_per_unit"] == "250.00"

    scam = client.get(f"/api/v1/dealer-products/{listing['id']}/scam-shield", headers=auth_headers(farmer_tokens)).json()
    assert scam["price_per_unit"] == "250.00"
    assert scam["reference_price_per_unit"] == "100.00"


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

"""D90-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from tests.conftest import auth_headers


def test_database_market_provider_matches_the_direct_repository_query(db_session, client, admin_tokens):
    """Non-regression: DatabaseMarketProvider must produce identical
    results to the previous direct-query path it replaced."""
    from app.repositories import product_repository
    from app.services.market.database_market_provider import DatabaseMarketProvider
    from tests.marketplace_factories import valid_product_payload

    product = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()
    client.post(f"/api/v1/products/{product['id']}/approve", json={}, headers=auth_headers(admin_tokens))
    client.post(
        f"/api/v1/products/{product['id']}/reference-prices",
        json={"product_id": product["id"], "price": "77.50", "source_type": "admin_entered_reference", "effective_date": "2026-01-01"},
        headers=auth_headers(admin_tokens),
    )

    import uuid

    product_id = uuid.UUID(product["id"])
    direct = product_repository.get_latest_reference_price(db_session, product_id)
    via_provider = DatabaseMarketProvider().get_reference_price(db_session, product_id=product_id)

    assert via_provider.available is True
    assert via_provider.price == direct.price
    assert via_provider.source_name == direct.source_name
    assert via_provider.effective_date == direct.effective_date


def test_database_market_provider_reports_unavailable_honestly_when_no_reference_price_exists(db_session, client, admin_tokens):
    from app.services.market.database_market_provider import DatabaseMarketProvider
    from tests.marketplace_factories import valid_product_payload
    import uuid

    product = client.post("/api/v1/products", json=valid_product_payload(), headers=auth_headers(admin_tokens)).json()
    client.post(f"/api/v1/products/{product['id']}/approve", json={}, headers=auth_headers(admin_tokens))

    result = DatabaseMarketProvider().get_reference_price(db_session, product_id=uuid.UUID(product["id"]))
    assert result.available is False
    assert result.price is None
    assert result.unavailable_reason is not None

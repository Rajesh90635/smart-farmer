import uuid


def valid_product_payload(**overrides):
    payload = {
        "name": "Test Product " + uuid.uuid4().hex[:8],
        "category": "crop_protection_product",
        "manufacturer": "Test Mfg",
        "pack_size_value": 500,
        "pack_size_unit": "ml",
    }
    payload.update(overrides)
    return payload


def valid_dealer_listing_payload(product_id: str, **overrides):
    payload = {"product_id": product_id, "price": "250.00", "stock_quantity": 100}
    payload.update(overrides)
    return payload

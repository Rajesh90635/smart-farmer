def valid_harvest_listing_payload(**overrides):
    payload = {
        "quantity_available": "1000.00",
        "unit": "kg",
        "quality_grade": "Grade A",
        "delivery_option": "buyer_collection",
        "service_area": {"state": "Kerala", "district": "Thrissur"},
    }
    payload.update(overrides)
    return payload


def valid_buyer_payload(**overrides):
    payload = {
        "display_name": "Test Buyer",
        "buyer_type": "wholesaler",
        "crops_purchased": [],
        "min_quantity": "100.00",
        "max_quantity": "5000.00",
    }
    payload.update(overrides)
    return payload


def valid_offer_payload(**overrides):
    payload = {"quantity": "500.00", "unit": "kg", "price_per_unit": "30.00"}
    payload.update(overrides)
    return payload

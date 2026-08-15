def valid_farm_payload(**overrides):
    payload = {
        "farm_name": "Test Farm",
        "description": "A test farm",
        "latitude": "10.850000",
        "longitude": "76.271000",
        "area_value": "2.5",
        "area_unit": "acre",
    }
    payload.update(overrides)
    return payload


def valid_plot_payload(**overrides):
    payload = {
        "plot_name": "North Plot",
        "area_value": "1.0",
        "area_unit": "acre",
        "soil_type": "loamy",
        "irrigation_type": "drip",
    }
    payload.update(overrides)
    return payload


def valid_crop_cycle_payload(crop_id: str, **overrides):
    payload = {
        "crop_id": crop_id,
        "season": "kharif",
        "sowing_date": "2026-06-01",
        "expected_harvest_date": "2026-09-01",
        "seed_variety": "Hybrid-1",
    }
    payload.update(overrides)
    return payload

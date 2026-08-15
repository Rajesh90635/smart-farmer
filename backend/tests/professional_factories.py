import uuid


def unique_phone() -> str:
    return "9" + str(uuid.uuid4().int)[:9]


def valid_professional_payload(**overrides):
    payload = {
        "role": "expert",
        "display_name": "Test Expert",
        "language_codes": ["en"],
        "crop_specialization_ids": [],
        "disease_specialization_categories": ["fungal"],
        "service_area": {"state": "Kerala", "district": "Thrissur"},
    }
    payload.update(overrides)
    return payload


def valid_case_payload(crop_cycle_id: str, **overrides):
    payload = {
        "crop_cycle_id": crop_cycle_id,
        "requested_professional_role": "expert",
        "reason": "farmer_requested",
        "consent_shared_items": ["crop_photo", "ai_result", "crop_stage"],
    }
    payload.update(overrides)
    return payload

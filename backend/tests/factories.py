import uuid

import pytest


def unique_phone() -> str:
    # 10-digit synthetic number, unique per test to avoid collisions.
    return "9" + str(uuid.uuid4().int)[:9]


@pytest.fixture()
def valid_register_payload():
    def _make(**overrides):
        payload = {
            "phone_number": unique_phone(),
            "password": "Str0ngPass",
            "full_name": "Test Farmer",
            "preferred_language_code": "en",
            "consents": [
                {"consent_type": "terms_of_service", "version": "1.0"},
                {"consent_type": "privacy_policy", "version": "1.0"},
            ],
        }
        payload.update(overrides)
        return payload

    return _make

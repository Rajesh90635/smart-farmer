"""
Phone number normalization tests - covers exactly the scenarios from the
live end-to-end investigation that found this bug (register with one
format, login with a differently-formatted-but-equivalent number).

Every test generates its own fresh 10-digit base number (reusing the same
unique_phone() convention already established in tests/factories.py) -
NOT a fixed literal - so the tests remain correct across repeated runs
against the same persistent test database, exactly like every other test
in this suite already does.
"""
import pytest

from app.core.phone_utils import normalize_phone_number
from tests.factories import unique_phone


def _register(client, phone_number, password="Test1234", full_name="Test Farmer"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": phone_number,
            "password": password,
            "full_name": full_name,
            "preferred_language_code": "en",
            "consents": [
                {"consent_type": "terms_of_service", "version": "1.0"},
                {"consent_type": "privacy_policy", "version": "1.0"},
            ],
        },
    )


def _login(client, phone_number, password="Test1234"):
    return client.post("/api/v1/auth/login", json={"phone_number": phone_number, "password": password})


def test_register_with_canonical_plus_91_format(client):
    response = _register(client, f"+91{unique_phone()}")
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_login_with_canonical_plus_91_format(client):
    base = unique_phone()
    _register(client, f"+91{base}")
    response = _login(client, f"+91{base}")
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_without_plus_prefix_finds_the_same_account_registered_with_plus(client):
    """THE bug reproduced live against the running backend before this
    fix existed: registered WITH +, login WITHOUT +."""
    base = unique_phone()
    _register(client, f"+91{base}")
    response = _login(client, f"91{base}")
    assert response.status_code == 200, f"Expected the +91-registered account to be found by a 91-prefixed (no +) login: {response.text}"
    assert "access_token" in response.json()


def test_login_with_bare_10_digit_number_finds_the_same_plus91_registered_account(client):
    """The third accepted format (bare 10 digits, no country code at
    all) must ALSO resolve to the same account."""
    base = unique_phone()
    _register(client, f"+91{base}")
    response = _login(client, base)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_without_plus_prefix_is_stored_canonically(client, db_session):
    base = unique_phone()
    response = _register(client, f"91{base}")
    assert response.status_code == 201

    from app.models.user import User

    canonical = f"+91{base}"
    user = db_session.query(User).filter(User.phone_number == canonical).one_or_none()
    assert user is not None, f"Expected the stored phone_number to be canonicalized to {canonical}"

    # The RAW, unnormalized form must NOT exist as a separate row - there
    # is exactly one canonical row, not two different phone-number
    # strings for what a farmer considers "the same number".
    duplicate_raw_row = db_session.query(User).filter(User.phone_number == f"91{base}").one_or_none()
    assert duplicate_raw_row is None


def test_register_with_bare_10_digits_is_stored_canonically(client, db_session):
    base = unique_phone()
    response = _register(client, base)
    assert response.status_code == 201

    from app.models.user import User

    user = db_session.query(User).filter(User.phone_number == f"+91{base}").one_or_none()
    assert user is not None


def test_clearly_invalid_phone_number_is_still_rejected(client):
    response = _register(client, "not-a-phone")
    assert response.status_code == 422


def test_too_short_phone_number_is_rejected(client):
    response = _register(client, "12345")
    assert response.status_code == 422


def test_login_with_a_malformed_phone_number_returns_generic_invalid_credentials_not_a_500(client):
    """A malformed phone at LOGIN time (LoginRequest has no format
    validator, by design) must never crash or leak information - it's
    treated the same as "no such user" and falls through to the
    existing generic 401 path, exactly as it did before this fix (no
    new behavior introduced for genuinely bad input)."""
    response = _login(client, "not-a-phone-at-all")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_wrong_password_still_correctly_rejected_after_normalization_change(client):
    base = unique_phone()
    _register(client, f"+91{base}")
    response = _login(client, f"+91{base}", password="WrongPass1")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_duplicate_registration_detected_regardless_of_phone_format(client):
    """The SAME choke point (get_by_phone) that fixes login also fixes
    the duplicate-account check at registration - attempting to
    register the same logical number in a different format must be
    rejected as a duplicate, not silently create a second account."""
    base = unique_phone()
    first = _register(client, f"+91{base}")
    assert first.status_code == 201

    duplicate_attempt = _register(client, f"91{base}")
    assert duplicate_attempt.status_code == 409
    assert duplicate_attempt.json()["error"]["code"] == "DUPLICATE_ACCOUNT"


class TestNormalizePhoneNumberUnit:
    """Pure unit tests for the helper itself - these use fixed literals
    safely, since normalize_phone_number() is a pure function with no
    database/state, so repeated runs can never collide."""

    def test_already_canonical_is_unchanged(self):
        assert normalize_phone_number("+919876500456") == "+919876500456"

    def test_91_prefix_without_plus_is_normalized(self):
        assert normalize_phone_number("919876500456") == "+919876500456"

    def test_bare_10_digit_indian_mobile_is_normalized(self):
        assert normalize_phone_number("9876545678") == "+919876545678"

    def test_whitespace_and_separators_are_tolerated(self):
        assert normalize_phone_number("+91 98765 00456") == "+919876500456"
        assert normalize_phone_number("+91-98765-00456") == "+919876500456"

    def test_invalid_input_raises_value_error(self):
        for bad in ["not-a-phone", "12345", "", None, "+91987650045", "+9198765004567"]:
            with pytest.raises(ValueError):
                normalize_phone_number(bad)

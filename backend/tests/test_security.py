import pytest

from app.core.jwt import TokenError, create_access_token, decode_access_token
from app.core.security_passwords import hash_password, verify_password


def test_password_hash_and_verify_round_trip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_hash_is_not_plaintext():
    hashed = hash_password("hunter2")
    assert hashed != "hunter2"


def test_jwt_round_trip():
    token = create_access_token(subject="farmer-123", role="farmer")
    payload = decode_access_token(token)
    assert payload["sub"] == "farmer-123"
    assert payload["role"] == "farmer"


def test_jwt_rejects_tampered_token():
    token = create_access_token(subject="farmer-123", role="farmer")
    header, payload, signature = token.split(".")
    # Flip the middle signature character, not the last one or two: base64's final
    # character carries unused padding bits that don't affect the decoded signature
    # bytes, so tampering only the tail can (rarely, ~1/1600) leave the signature
    # byte-for-byte unchanged and make this test spuriously pass. A middle character
    # is always byte-significant.
    mid = len(signature) // 2
    replacement = "A" if signature[mid] != "A" else "B"
    tampered_signature = signature[:mid] + replacement + signature[mid + 1 :]
    tampered = f"{header}.{payload}.{tampered_signature}"
    with pytest.raises(TokenError):
        decode_access_token(tampered)

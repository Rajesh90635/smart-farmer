"""
Refresh tokens are opaque random strings (NOT JWTs) - there's no need for
them to be self-describing, and keeping them opaque means a stolen token
reveals nothing about its owner. Only the SHA-256 hash is ever persisted.
"""
import hashlib
import secrets

_TOKEN_BYTES = 48  # 384 bits of entropy


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

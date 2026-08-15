"""
Password hashing abstraction.

Note: the MVP's primary farmer login path is phone + OTP (per the approved
architecture), not passwords — but several roles (admin, expert, dealer,
buyer back-office logins) will likely use password auth, so this foundation
exists now rather than being bolted on ad hoc later. Bcrypt via passlib is
used because it's a well-reviewed, free, standard choice with sane defaults.
"""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_MIN_PASSWORD_LENGTH = 8


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def is_strong_password(password: str) -> bool:
    """Minimum bar, not a full complexity policy: at least 8 characters,
    containing at least one letter and one digit. Deliberately not
    stricter than this — an overly strict policy pushes farmers toward
    writing passwords down, which is a worse security outcome."""
    if len(password) < _MIN_PASSWORD_LENGTH:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit


# Precomputed once so a login attempt against a non-existent phone number
# still runs a real bcrypt verify (against a hash of a value the attacker
# doesn't know) - keeps invalid-credentials response time closer to the
# real-account-wrong-password path so timing doesn't reveal whether the
# account exists.
DUMMY_PASSWORD_HASH = hash_password("dummy-password-used-only-for-timing-safety")

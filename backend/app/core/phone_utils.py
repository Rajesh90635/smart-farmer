"""
Phone number normalization - the ONE place this logic lives, per the
explicit product decision: this application serves Indian farmers, and
every phone number is canonicalized to E.164 format with the +91 country
code. This is what makes "+919876543210" and "919876543210" (and, for a
bare 10-digit number, "9876543210") resolve to the SAME account rather
than silently being treated as different users - the exact bug this
module was written to fix, reproduced live against the running backend
before this fix was written.

This function is used in exactly two places, both by design:
1. app/schemas/auth.py:RegisterRequest - normalizes BEFORE storage, so
   the database always holds the canonical form for new accounts.
2. app/repositories/user_repository.py:get_by_phone - normalizes BEFORE
   every lookup, so a query using any of the accepted input formats
   still finds the canonically-stored row.

Do not call this from anywhere else without good reason - if a third
call site is ever needed, this is still the only place the actual rule
should be encoded (one reusable helper, do not duplicate).
"""
import re

_DIGITS_ONLY = re.compile(r"^[0-9]+$")


def normalize_phone_number(raw: str) -> str:
    """
    Canonicalizes a phone number to +91XXXXXXXXXX (E.164, India-only, per
    the approved product decision - this application does not currently
    support farmers outside India).

    Accepted input forms:
    - "+919876543210"  (already canonical - re-validated, returned as-is)
    - "919876543210"   (91 + 10 digits, no leading + )
    - "9876543210"     (bare 10-digit Indian mobile number - country code
      is implicit and added)

    Raises ValueError for anything that doesn't unambiguously match one
    of these three forms - this is NOT a general international phone
    parser, and deliberately does not try to guess a country for a
    number that doesn't look like one of the above.
    """
    if raw is None:
        raise ValueError("Phone number is required.")

    cleaned = re.sub(r"[\s\-()]", "", raw.strip())

    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if not _DIGITS_ONLY.match(digits):
            raise ValueError("Phone number must contain only digits after '+'.")
        if digits.startswith("91") and len(digits) == 12:
            return f"+{digits}"
        raise ValueError("Phone number must be a valid +91 Indian mobile number.")

    if not _DIGITS_ONLY.match(cleaned):
        raise ValueError("Phone number must contain only digits.")

    if len(cleaned) == 10:
        return f"+91{cleaned}"

    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"

    raise ValueError(
        "Phone number must be a 10-digit Indian mobile number, "
        "optionally prefixed with '91' or '+91'."
    )

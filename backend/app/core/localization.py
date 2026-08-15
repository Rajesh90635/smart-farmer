"""
Centralized language-code vocabulary.

Per the localization architecture (docs/LOCALIZATION.md), language logic
must not be hard-coded ad hoc throughout the app. Every place that needs to
validate or enumerate supported languages imports from here — the mobile
app's `.arb` files (see mobile/lib/l10n/) are expected to track this same
list, one language at a time, as each is actually translated.
"""

# English is the only fully-translated language today (mobile/lib/l10n/app_en.arb).
# The others are pre-registered as *backend-valid* codes so a farmer's
# preferred_language_code can be set ahead of the UI translation actually
# shipping - the approved architecture's target-language decision (which of
# these gets translated first) is still an open question, not decided here.
SUPPORTED_LANGUAGE_CODES: frozenset[str] = frozenset({
    "en",  # English
    "hi",  # Hindi
    "kn",  # Kannada
    "te",  # Telugu
    "ta",  # Tamil
    "ml",  # Malayalam
    "mr",  # Marathi
})

DEFAULT_LANGUAGE_CODE = "en"


def is_supported_language(code: str) -> bool:
    return code in SUPPORTED_LANGUAGE_CODES

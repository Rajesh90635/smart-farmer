"""
Safety validator. Two jobs:
1. Check the INCOMING farmer message for a chemical/dosage/prescription
   request BEFORE intent routing even happens - these never reach normal
   tool-based routing at all, they always get the same safe redirect.
2. Check the OUTGOING composed response for prescription-like or
   over-certain language as defense-in-depth, even though template-based
   responses should never contain this by construction.
"""
import re

_PRESCRIPTION_TRIGGER_PATTERNS = [
    r"\bwhat (pesticide|fungicide|herbicide|insecticide|chemical|fertilizer|medicine|drug)\b",
    r"\b(pesticide|fungicide|herbicide|insecticide) (dose|dosage|amount|quantity|ml|mg)\b",
    r"\bhow much (pesticide|fungicide|herbicide|insecticide|chemical|fertilizer) (should|do) i (use|apply|spray)\b",
    r"\bwhich (pesticide|fungicide|herbicide|insecticide|chemical) (should|to) (i )?(use|apply|buy)\b",
    r"\bcure (my|the) (crop|plant|disease)\b",
    r"\bhow (do|to) i (kill|treat) (the )?(pest|disease|fungus|insect)\b",
]

_UNSAFE_OUTPUT_PATTERNS = [
    r"\bapply \d+\s*(ml|mg|g|kg|l)\b",
    r"\bmix \d+\s*(ml|mg|g|kg|l)\b",
    r"\b(spray|apply) [\w\s]+ at \d+",
]


def is_prescription_request(message: str) -> bool:
    text = message.lower()
    return any(re.search(pattern, text) for pattern in _PRESCRIPTION_TRIGGER_PATTERNS)


def contains_unsafe_prescription_language(response_text: str) -> bool:
    text = response_text.lower()
    return any(re.search(pattern, text) for pattern in _UNSAFE_OUTPUT_PATTERNS)

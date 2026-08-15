"""
ConfidenceEvaluator: maps a raw confidence score to HIGH/MEDIUM/LOW.

Per Requirement 11: thresholds must come from evaluation, not be picked
arbitrarily and called "safe." Since no trained model and no validation
dataset exist yet (see docs/AI_EVALUATION.md), the threshold values below
are PLACEHOLDERS - conservative defaults chosen to bias toward
`requires_review` rather than false confidence, but they carry no
evaluation backing. They are configurable via Settings specifically so
they can be replaced with evaluation-derived values without a code change
once a real validation dataset exists - never adjust the numeric literals
here without updating docs/AI_EVALUATION.md's justification section.
"""
import enum

from app.core.config import Settings


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def classify_confidence(confidence: float, settings: Settings) -> ConfidenceLevel:
    if confidence >= settings.ai_confidence_high_threshold:
        return ConfidenceLevel.HIGH
    if confidence >= settings.ai_confidence_medium_threshold:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW

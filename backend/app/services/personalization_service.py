"""
Phase 39: Farmer Personalization Profile.

Every preference is computed on-read from REAL historical data across
ALL of the farmer's crop cycles - nothing here is persisted as a
"belief," so it can never go stale or be mistaken for ground truth. This
mirrors the exact same compute-on-read convention already established
for Phase 33's risk score and Phase 38's performance score.

EVIDENCE THRESHOLDS (deterministic, explicitly disclosed as placeholders
pending real-world validation):
- evidence_count < 3  -> INSUFFICIENT_DATA (no preference stated at all)
- evidence_count 3-6  -> LOW confidence
- evidence_count 7-14 -> MEDIUM confidence
- evidence_count >=15 -> HIGH confidence

A single historical event NEVER becomes a stated preference - the
minimum-evidence floor of 3 is enforced everywhere below.
"""
import uuid
from collections import Counter

from sqlalchemy.orm import Session

from app.models.task import TaskStatus
from app.repositories import advisory_feedback_repository, crop_cycle_repository, task_repository, treatment_repository
from app.schemas.personalization import LearnedPreference, PersonalizationProfileResponse


def _confidence_for(evidence_count: int) -> str | None:
    if evidence_count < 3:
        return None
    if evidence_count < 7:
        return "low"
    if evidence_count < 15:
        return "medium"
    return "high"


def get_personalization_profile(db: Session, farmer_id: str) -> PersonalizationProfileResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycles = crop_cycle_repository.list_all_for_farmer(db, farmer_uuid)

    preferences = [
        _preferred_crop_signal(crop_cycles),
        _treatment_follow_up_signal(db, farmer_uuid, crop_cycles),
        _task_completion_signal(db, farmer_uuid, crop_cycles),
        _advisory_feedback_signal(db, farmer_uuid),
    ]

    return PersonalizationProfileResponse(farmer_id=farmer_uuid, preferences=preferences)


def _preferred_crop_signal(crop_cycles) -> LearnedPreference:
    evidence_count = len(crop_cycles)
    confidence = _confidence_for(evidence_count)
    if confidence is None:
        return LearnedPreference(
            signal_name="preferred_crop",
            observation=None,
            evidence_count=evidence_count,
            confidence=None,
            last_observed_at=None,
            explanation=f"Only {evidence_count} crop cycle(s) recorded - at least 3 are needed before a crop preference can be identified.",
        )

    counts = Counter(cc.crop_id for cc in crop_cycles)
    most_common_crop_id, count = counts.most_common(1)[0]
    most_recent = max(crop_cycles, key=lambda cc: cc.created_at)
    return LearnedPreference(
        signal_name="preferred_crop",
        observation=f"Most frequently cultivated crop appears in {count} of {evidence_count} recorded crop cycles.",
        evidence_count=evidence_count,
        confidence=confidence,
        last_observed_at=most_recent.created_at,
        explanation=f"Based on {evidence_count} recorded crop cycles for this farmer.",
    )


def _treatment_follow_up_signal(db: Session, farmer_uuid: uuid.UUID, crop_cycles) -> LearnedPreference:
    all_treatments = []
    for cc in crop_cycles:
        all_treatments.extend(treatment_repository.list_treatments_for_crop_cycle(db, cc.id, farmer_uuid))

    evidence_count = len(all_treatments)
    confidence = _confidence_for(evidence_count)
    if confidence is None:
        return LearnedPreference(
            signal_name="treatment_follow_up_consistency",
            observation=None,
            evidence_count=evidence_count,
            confidence=None,
            last_observed_at=None,
            explanation=f"Only {evidence_count} treatment(s) recorded - at least 3 are needed before a follow-up pattern can be identified.",
        )

    with_follow_up = sum(1 for t in all_treatments if treatment_repository.list_follow_ups_for_treatment(db, t.id, farmer_uuid))
    ratio = with_follow_up / evidence_count
    if ratio >= 0.7:
        observation = "This farmer consistently records a follow-up after applying treatments."
    elif ratio >= 0.3:
        observation = "This farmer sometimes records a follow-up after applying treatments."
    else:
        observation = "This farmer rarely records a follow-up after applying treatments."

    most_recent = max(all_treatments, key=lambda t: t.created_at)
    return LearnedPreference(
        signal_name="treatment_follow_up_consistency",
        observation=observation,
        evidence_count=evidence_count,
        confidence=confidence,
        last_observed_at=most_recent.created_at,
        explanation=f"Based on {with_follow_up} of {evidence_count} recorded treatments having a follow-up.",
    )


def _task_completion_signal(db: Session, farmer_uuid: uuid.UUID, crop_cycles) -> LearnedPreference:
    all_tasks = []
    for cc in crop_cycles:
        all_tasks.extend(task_repository.list_for_crop_cycle(db, cc.id, farmer_uuid))

    resolved_tasks = [t for t in all_tasks if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)]
    evidence_count = len(resolved_tasks)
    confidence = _confidence_for(evidence_count)
    if confidence is None:
        return LearnedPreference(
            signal_name="task_completion_consistency",
            observation=None,
            evidence_count=evidence_count,
            confidence=None,
            last_observed_at=None,
            explanation=f"Only {evidence_count} resolved task(s) recorded - at least 3 are needed before a completion pattern can be identified.",
        )

    completed = sum(1 for t in resolved_tasks if t.status == TaskStatus.COMPLETED)
    ratio = completed / evidence_count
    if ratio >= 0.7:
        observation = "This farmer usually completes recorded tasks rather than cancelling them."
    elif ratio >= 0.3:
        observation = "This farmer sometimes completes recorded tasks."
    else:
        observation = "This farmer often cancels recorded tasks rather than completing them."

    most_recent = max(resolved_tasks, key=lambda t: t.created_at)
    return LearnedPreference(
        signal_name="task_completion_consistency",
        observation=observation,
        evidence_count=evidence_count,
        confidence=confidence,
        last_observed_at=most_recent.created_at,
        explanation=f"Based on {completed} of {evidence_count} resolved tasks being completed (vs. cancelled).",
    )


def _advisory_feedback_signal(db: Session, farmer_uuid: uuid.UUID) -> LearnedPreference:
    feedback = advisory_feedback_repository.list_for_farmer(db, farmer_uuid)
    evidence_count = len(feedback)
    confidence = _confidence_for(evidence_count)
    if confidence is None:
        return LearnedPreference(
            signal_name="advisory_feedback_ratio",
            observation=None,
            evidence_count=evidence_count,
            confidence=None,
            last_observed_at=None,
            explanation=f"Only {evidence_count} feedback record(s) submitted - at least 3 are needed before a pattern can be identified.",
        )

    helpful = sum(1 for f in feedback if f.feedback_type.value == "helpful")
    ratio = helpful / evidence_count
    if ratio >= 0.7:
        observation = "This farmer generally finds advisory recommendations helpful."
    elif ratio >= 0.3:
        observation = "This farmer has mixed feedback on advisory recommendations."
    else:
        observation = "This farmer generally does not find advisory recommendations helpful."

    most_recent = max(feedback, key=lambda f: f.created_at)
    return LearnedPreference(
        signal_name="advisory_feedback_ratio",
        observation=observation,
        evidence_count=evidence_count,
        confidence=confidence,
        last_observed_at=most_recent.created_at,
        explanation=f"Based on {helpful} of {evidence_count} feedback submissions marked helpful.",
    )

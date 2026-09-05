"""
NearbyProfessionalService: ranks VERIFIED professionals for a case. Never
ranks solely by distance - a weighted score combining verification (a hard
filter, not a score component), availability, crop/disease expertise
match, language match, service-area match, workload, and reputation.

ABSOLUTE RULE enforced here: only VERIFIED professionals are ever
candidates - unverified/rejected/suspended/expired professionals are
excluded at the repository query level (candidates_for_matching only
selects VERIFIED rows), not filtered out after the fact where a bug could
let one slip through.
"""
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile
from app.repositories import professional_repository
from app.repositories.case_repository import count_active_assignments_for_professional


@dataclass(frozen=True)
class MatchCriteria:
    role: str
    crop_id: uuid.UUID | None = None
    disease_category: str | None = None
    language_code: str | None = None
    state: str | None = None
    district: str | None = None
    exclude_professional_ids: frozenset = frozenset()


@dataclass(frozen=True)
class RankedCandidate:
    professional: ProfessionalProfile
    score: float
    reason: str


def find_ranked_candidates(db: Session, criteria: MatchCriteria, settings: Settings) -> list[RankedCandidate]:
    candidates = professional_repository.candidates_for_matching(db, criteria.role)

    ranked: list[RankedCandidate] = []
    for professional in candidates:
        if professional.id in criteria.exclude_professional_ids:
            continue

        # D34-01 (docs/audit/c06_expert_network.md): OFFLINE was
        # previously only soft-scored (0 points), so an OFFLINE
        # professional could still win and be auto-assigned a case if
        # ranked highest/sole candidate. A professional who has
        # explicitly signaled they're unavailable must never be handed a
        # new case automatically.
        if professional.availability_status == AvailabilityStatus.OFFLINE:
            continue

        active_count = count_active_assignments_for_professional(db, professional.id)
        if active_count >= professional.max_active_cases:
            continue

        score = 0.0
        reasons = []

        if professional.availability_status == AvailabilityStatus.AVAILABLE:
            score += 30
            reasons.append("available")
        elif professional.availability_status == AvailabilityStatus.BUSY:
            score += 5

        if criteria.crop_id is not None and professional.crop_specialization_ids and str(criteria.crop_id) in professional.crop_specialization_ids:
            score += 25
            reasons.append("crop match")

        if criteria.disease_category is not None and professional.disease_specialization_categories and criteria.disease_category in professional.disease_specialization_categories:
            score += 20
            reasons.append("disease expertise match")

        if criteria.language_code is not None and professional.language_codes and criteria.language_code in professional.language_codes:
            score += 20
            reasons.append("language match")

        area = professional.service_area or {}
        if criteria.district is not None and area.get("district") == criteria.district:
            score += 15
            reasons.append("service area match")
        elif criteria.state is not None and area.get("state") == criteria.state:
            score += 5
            reasons.append("same state")

        score += min(professional.completed_case_count, 20) * 0.25
        score += max(0, (professional.max_active_cases - active_count)) * 0.5

        ranked.append(RankedCandidate(professional=professional, score=score, reason=", ".join(reasons) or "verified professional"))

    # Tiebreaker for equally-scored candidates: prefer the most recently
    # registered verified professional. This resolves ties deterministically
    # (found via a real test failure: with multiple equally-qualified
    # experts in the pool, matching was effectively arbitrary/DB-order-
    # dependent) and is a defensible real-world choice too - it gives
    # newer verified professionals a genuine chance to receive cases
    # rather than always losing ties to whoever registered first.
    ranked.sort(key=lambda c: (c.score, c.professional.created_at), reverse=True)
    return ranked

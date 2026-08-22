"""
Phase 36: crop-cycle-SCOPED tool functions for the Context-Aware AI Crop
Assistant. These mirror the exact dict-shape convention already
established in tools.py (farmer-wide) - {"available": bool, "source":
str, ...} - but scoped to ONE specific crop_cycle_id instead of "the
farmer's most recent active crop."

Every function reuses an EXISTING, already-tested service/repository
directly - none of these recompute anything Phase 29/31/33/34/35 already
computed. Financial, treatment, and disease-confidence values are always
passed through VERBATIM from the underlying service - never reworded,
recalculated, or upgraded in certainty.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories import ai_analysis_repository, treatment_repository
from app.services import crop_financial_service, treatment_service
from app.services.ai.confidence import classify_confidence


def get_crop_scoped_disease_status(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, settings: Settings) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    if not analyses:
        return {"available": False, "source": "AI disease detection (this crop)"}

    analysis = max(analyses, key=lambda a: a.created_at)
    confidence_level = classify_confidence(analysis.confidence, settings).value if analysis.confidence is not None else None
    return {
        "available": True,
        "source": "AI disease detection (this crop)",
        "result_status": analysis.result_status.value,
        "predicted_class": analysis.predicted_class,
        "confidence_level": confidence_level,
        "requires_review": analysis.requires_review,
    }


def get_crop_scoped_treatment_status(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> dict:
    farmer_uuid = uuid.UUID(farmer_id)
    treatments = treatment_repository.list_treatments_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    if not treatments:
        return {"available": False, "source": "Treatment records (this crop)"}

    most_recent = treatments[0]
    follow_ups = treatment_repository.list_follow_ups_for_treatment(db, most_recent.id, farmer_uuid)

    result = {
        "available": True,
        "source": "Treatment records (this crop)",
        "application_date": most_recent.application_date.isoformat(),
        "has_follow_up": bool(follow_ups),
    }
    if follow_ups:
        effectiveness = treatment_service.get_effectiveness(db, farmer_id, most_recent.id)
        result["effectiveness_result"] = effectiveness.result
        result["effectiveness_summary"] = effectiveness.basis
    return result


def get_crop_scoped_financial_status(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> dict:
    summary = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle_id)
    if summary.estimated_cost is None:
        estimate_note = "No cost estimate has been entered, so I can't tell you if you're over or under budget."
    elif summary.cost_variance is not None and summary.cost_variance < 0:
        estimate_note = f"This is {abs(summary.cost_variance)} over your estimated cost."
    elif summary.cost_variance is not None:
        estimate_note = f"You are {summary.cost_variance} under your estimated cost."
    else:
        estimate_note = ""

    return {
        "available": True,
        "source": "Crop financial summary (Phase 31)",
        "actual_cost": str(summary.actual_cost),
        "estimate_note": estimate_note,
    }


def get_crop_scoped_harvest_status(db, crop_cycle_id: uuid.UUID) -> dict:
    from app.repositories import harvest_repository

    harvests = harvest_repository.list_harvests_by_crop_cycle(db, crop_cycle_id)
    if not harvests:
        return {"available": False, "source": "Harvest records (this crop)"}
    harvest = harvests[0]
    return {
        "available": True,
        "source": "Harvest records (this crop)",
        "status": harvest.status.value,
    }

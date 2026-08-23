"""
Phase 36: Context-Aware AI Crop Assistant.

Reuses the EXISTING deterministic intent router (extended with two new
intents, not a competing implementation), the EXISTING response
templating system, and the EXISTING prescription-safety validator -
nothing here is a second AI-provider architecture. The only genuinely
new pieces are the crop-cycle-SCOPED tool functions (crop_context_tools
.py), since the original farmer-wide assistant (Prompt 11) predates
Phases 29-35 and has no way to answer about a SPECIFIC crop cycle.

DELIBERATELY STATELESS: no conversation is persisted. The farmer-wide
assistant already has full history; this narrower feature doesn't need
its own, per the explicit "prefer stateless unless proven necessary"
guidance.

CONTEXT ISOLATION: every tool call below is scoped to the ONE verified
crop_cycle_id resolved at the top of this function - there is no code
path here that could pull data from a different crop cycle or a
different farmer.

The AIProvider abstraction for GENERAL_AGRICULTURE (open-ended
questions) exists in this codebase but was NEVER actually wired into the
existing farmer-wide assistant either (confirmed by inspection - no call
site exists anywhere). This crop-scoped assistant matches that same,
already-established precedent rather than being the first to newly
connect an unused abstraction - GENERAL_AGRICULTURE honestly returns
"not available" here too.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.farmer_messages import get_message
from app.repositories import crop_cycle_repository
from app.schemas.crop_assistant import CropAssistantRequest, CropAssistantResponse
from app.services.assistant import crop_context_tools
from app.services.assistant.intent_router import Intent, detect_intent
from app.services.assistant.response_generator import generate_response
from app.services.assistant.safety_validator import contains_unsafe_prescription_language, is_prescription_request


def ask_crop_assistant(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: CropAssistantRequest, settings: Settings) -> CropAssistantResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    language_code = "en"

    if is_prescription_request(payload.question):
        return CropAssistantResponse(
            crop_cycle_id=crop_cycle_id,
            intent="prescription_blocked",
            answer=get_message("assistant_prescription_redirect", language_code),
            context_used=[],
            limitations=[],
        )

    intent = detect_intent(payload.question)
    tool_result = _call_tool_for_intent(db, farmer_id, crop_cycle, intent, settings)
    response_text, _confidence, sources = generate_response(intent, tool_result, language_code)

    if contains_unsafe_prescription_language(response_text):
        response_text = get_message("assistant_prescription_redirect", language_code)
        sources = []

    limitations = []
    if not tool_result.get("available", True):
        limitations.append("No data was available in Smart Farmer for this specific question.")
    if tool_result.get("confidence_level") == "low":
        limitations.append("The underlying analysis had low confidence - treat this as inconclusive, not a confirmed diagnosis.")

    return CropAssistantResponse(
        crop_cycle_id=crop_cycle_id,
        intent=intent.value,
        answer=response_text,
        context_used=sources,
        limitations=limitations,
    )


def _call_tool_for_intent(db: Session, farmer_id: str, crop_cycle, intent: Intent, settings: Settings) -> dict:
    if intent == Intent.CROP_STATUS:
        return {
            "available": True,
            "source": "This crop's record",
            "crop_name": crop_cycle.crop.name,
            "farm_name": crop_cycle.plot.farm.farm_name,
            "stage": crop_cycle.cultivation_status.value,
        }
    if intent == Intent.DISEASE_STATUS:
        return crop_context_tools.get_crop_scoped_disease_status(db, farmer_id, crop_cycle.id, settings)
    if intent == Intent.TREATMENT_STATUS:
        return crop_context_tools.get_crop_scoped_treatment_status(db, farmer_id, crop_cycle.id)
    if intent == Intent.FINANCIAL_STATUS:
        return crop_context_tools.get_crop_scoped_financial_status(db, farmer_id, crop_cycle.id)
    if intent in (Intent.HARVEST_READINESS, Intent.HARVEST_STATUS):
        return crop_context_tools.get_crop_scoped_harvest_status(db, crop_cycle.id)
    if intent == Intent.HELP:
        return {}
    return {}

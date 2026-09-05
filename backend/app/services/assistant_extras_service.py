"""
Feedback, preferences, and the daily summary - all built from real tool
data, same as chat responses. The daily summary is a read-only
composition of the same tools used by chat - no separate
summary-generation logic that could drift from what chat itself reports.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.farmer_messages import get_message
from app.core.localization import is_supported_language
from app.models.assistant_feedback import AssistantFeedback, AssistantPreference
from app.repositories import assistant_repository, user_repository
from app.schemas.assistant import DailySummaryResponse, FeedbackCreateRequest, PreferenceResponse, PreferenceUpdateRequest
from app.services import crop_financial_service, crop_risk_service
from app.services.assistant import tools
from app.services.weather.weather_provider import WeatherProvider


def submit_feedback(db: Session, farmer_id: str, message_id: uuid.UUID, payload: FeedbackCreateRequest) -> None:
    message = assistant_repository.get_message_owned(db, message_id, uuid.UUID(farmer_id))
    if message is None:
        raise AppError(error_codes.NOT_FOUND, "Message not found.", 404)

    feedback = AssistantFeedback(message_id=message_id, farmer_id=uuid.UUID(farmer_id), feedback_type=payload.feedback_type, note=payload.note)
    assistant_repository.create_feedback(db, feedback)
    db.commit()


def get_or_create_preferences(db: Session, farmer_id: str) -> PreferenceResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    prefs = assistant_repository.get_preferences(db, farmer_uuid)
    if prefs is None:
        prefs = AssistantPreference(farmer_id=farmer_uuid)
        assistant_repository.create_preferences(db, prefs)
        db.commit()
        db.refresh(prefs)
    return PreferenceResponse.model_validate(prefs)


def update_preferences(db: Session, farmer_id: str, payload: PreferenceUpdateRequest) -> PreferenceResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    prefs = assistant_repository.get_preferences(db, farmer_uuid)
    if prefs is None:
        prefs = AssistantPreference(farmer_id=farmer_uuid)
        assistant_repository.create_preferences(db, prefs)
        db.flush()

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return PreferenceResponse.model_validate(prefs)


def get_daily_summary(
    db: Session, farmer_id: str, weather_provider: WeatherProvider, settings: Settings, *, language_code_override: str | None = None
) -> DailySummaryResponse:
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    profile_language_code = user.farmer_profile.preferred_language_code if user and getattr(user, "farmer_profile", None) else "en"

    # `language_code_override` lets a caller (the location-based audio
    # language feature) request the summary in a different language than
    # the farmer's saved profile preference, WITHOUT changing that saved
    # preference - e.g. a farmer traveling into a different linguistic
    # region hearing the briefing in that region's language once, not a
    # permanent profile change. Falls back to the profile language for any
    # unrecognized code rather than silently accepting an invalid one.
    language_code = language_code_override if language_code_override and is_supported_language(language_code_override) else profile_language_code

    lines: list[str] = []

    weather = tools.get_weather_status(db, farmer_id, weather_provider, settings)
    if weather.get("available"):
        lines.append(
            get_message(
                "daily_summary_weather",
                language_code,
                temp=weather.get("current_temperature_c", "?"),
                rain=weather.get("rain_probability_today_percent", "?"),
            )
        )

    crop = tools.get_crop_status(db, farmer_id)
    if crop.get("available"):
        lines.append(get_message("daily_summary_crop", language_code, crop_name=crop["crop_name"], stage=crop["stage"]))

    # D92-06/D93-04 (docs/audit/c13_governance_farmbrain_security.md):
    # get_disease_status already existed and was already used by the
    # chat assistant's DISEASE_STATUS intent, but was never included in
    # the daily summary composition - same "reuse an existing tool,
    # don't invent one" pattern as the expert-case line above. Only a
    # genuine DISEASE_DETECTED result is surfaced - healthy/low-confidence/
    # unknown results say nothing here (they carry no actionable urgency,
    # and low-confidence must never be presented as a finding).
    disease = tools.get_disease_status(db, farmer_id, settings)
    if disease.get("available") and disease["result_status"] == "disease_detected":
        lines.append(get_message("daily_summary_disease", language_code, predicted_class=disease["predicted_class"]))

    # D92-02/D93-01: crop_risk_service already aggregates disease/weather/
    # task/financial signals into one score for this exact crop cycle
    # (Phase 33) - only surfaced when it says something worth a farmer's
    # attention (medium/high), never "low"/"insufficient_data" noise.
    if crop.get("available"):
        risk = crop_risk_service.get_risk_score(
            db, farmer_id, uuid.UUID(crop["crop_cycle_id"]), weather_provider=weather_provider, settings=settings
        )
        if risk.overall_risk in ("medium", "high"):
            lines.append(get_message("daily_summary_risk", language_code, level=risk.overall_risk))

    # D92-08/D93-09: crop_financial_service already computes actual spend
    # for this crop cycle (Phase 31) - only surfaced once something has
    # actually been spent, consistent with every other line's "only
    # report what's actually there" discipline.
    if crop.get("available"):
        finance = crop_financial_service.get_financial_summary(db, farmer_id, uuid.UUID(crop["crop_cycle_id"]))
        if finance.actual_cost and finance.actual_cost > 0:
            lines.append(get_message("daily_summary_finance", language_code, actual_cost=finance.actual_cost))

    harvest = tools.get_harvest_status(db, farmer_id)
    if harvest.get("available") and harvest["status"] in ("approaching", "ready", "listed"):
        lines.append(get_message("daily_summary_harvest", language_code, status=harvest["status"]))

    offers = tools.get_buyer_offers(db, farmer_id)
    if offers.get("available") and offers["offer_count"] > 0:
        lines.append(get_message("daily_summary_marketplace", language_code, offer_count=offers["offer_count"]))

    delivery = tools.get_delivery_status(db, farmer_id)
    if delivery.get("available") and delivery["status"] not in ("delivered",):
        lines.append(get_message("daily_summary_delivery", language_code, status=delivery["status"]))

    # Added Step 14: the tool already existed (Prompt 11/Step 13's
    # get_expert_case_status) but was never included in the daily
    # summary composition - a real, minimal gap closed by reusing it
    # exactly like every other line above, not by building anything new.
    case = tools.get_expert_case_status(db, farmer_id)
    if case.get("available") and case["status"] not in ("closed", "cancelled"):
        lines.append(get_message("daily_summary_expert_review", language_code, status=case["status"]))

    # Added Step 16: reuses task_repository.list_overdue_for_farmer
    # directly (a simple count, not a farmer-question-answering tool, so
    # it doesn't need a new entry in tools.py's get_* function set) - the
    # same "only report what's actually there, no invented urgency"
    # discipline as every other line above.
    from app.repositories import task_repository

    overdue_tasks = task_repository.list_overdue_for_farmer(db, uuid.UUID(farmer_id), today=datetime.now(timezone.utc).date())
    if overdue_tasks:
        count = len(overdue_tasks)
        lines.append(get_message("daily_summary_tasks_overdue", language_code, count=count, plural="s" if count != 1 else ""))

    if not lines:
        lines.append(get_message("daily_summary_no_updates", language_code))

    return DailySummaryResponse(language_code=language_code, lines=lines, generated_at=datetime.now(timezone.utc))

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

# D92-09 (docs/audit/FINAL_CANONICAL_group_D.md): a genuine urgency
# ranking, not the fixed hardcoded composition order below - a CRITICAL
# disease alert must always outrank a routine harvest-approaching note
# even though "harvest" is composed earlier today. Higher number = higher
# urgency = appears first. Ties keep this function's own composition
# order (Python's sort is stable), so nothing shuffles unless a genuine
# severity difference calls for it.
_LINE_PRIORITY = {
    "disease": 100,
    "risk_high": 90,
    "tasks_overdue": 65,
    "risk_medium": 60,
    "harvest": 55,
    "expert_review": 50,
    "irrigation": 45,
    "weather_action": 40,
    "marketplace": 35,
    "delivery": 35,
    "finance": 30,
    "weather": 15,
    "crop": 15,
    "no_updates": 15,
    # Supplementary "what changed since last visit" detail lines - always
    # lower priority than the primary state lines above, since they're
    # elaborating on a change already summarized by the (separately
    # handled) changed-since-last-visit banner.
    "changed_detail": 10,
}


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

    # D92-09 (docs/audit/FINAL_CANONICAL_group_D.md): lines carry a
    # priority score at the point they're composed (see _LINE_PRIORITY)
    # and are reordered by it just before being returned - a CRITICAL
    # disease alert now always outranks a routine harvest-approaching
    # note, even though "harvest" is appended earlier in this function's
    # own fixed composition order. `scored_lines` never leaves this
    # function; `lines` (the final, reordered list of plain strings) is
    # what every existing caller/test still sees.
    scored_lines: list[tuple[int, str]] = []
    risk = None
    finance = None

    weather = tools.get_weather_status(db, farmer_id, weather_provider, settings)
    if weather.get("available"):
        scored_lines.append((
            _LINE_PRIORITY["weather"],
            get_message(
                "daily_summary_weather",
                language_code,
                temp=weather.get("current_temperature_c", "?"),
                rain=weather.get("rain_probability_today_percent", "?"),
            ),
        ))
        # D93-03 (docs/audit/FINAL_CANONICAL_group_D.md): the spray-advisory
        # crop_action field already existed on FarmWeatherResponse - it was
        # simply never surfaced in the daily brief. Only ever fires for
        # the one implemented action (avoid_spraying), same as the schema.
        if weather.get("crop_action"):
            scored_lines.append((_LINE_PRIORITY["weather_action"], get_message("daily_summary_weather_action", language_code)))

    # D92-04 (docs/audit/FINAL_CANONICAL_group_D.md): lists every one of
    # the farmer's active crop cycles (a multi-crop farm previously only
    # ever saw its single most-recently-updated cycle) - falls back to the
    # single-crop wording when there's only one, so a one-crop farmer's
    # daily brief reads exactly as before.
    crop_all = tools.get_all_active_crop_statuses(db, farmer_id)
    crop = {"available": False}
    if crop_all.get("available"):
        crops = crop_all["crops"]
        crop = {"available": True, "crop_cycle_id": crops[0]["crop_cycle_id"], "stage": crops[0]["stage"]}
        if len(crops) == 1:
            scored_lines.append((_LINE_PRIORITY["crop"], get_message("daily_summary_crop", language_code, crop_name=crops[0]["crop_name"], stage=crops[0]["stage"])))
        else:
            crop_summary = "; ".join(f"{c['crop_name']} ({c['stage']})" for c in crops)
            scored_lines.append((_LINE_PRIORITY["crop"], get_message("daily_summary_crop_multi", language_code, crop_summary=crop_summary)))

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
        scored_lines.append((_LINE_PRIORITY["disease"], get_message("daily_summary_disease", language_code, predicted_class=disease["predicted_class"])))

    # D92-02/D93-01: crop_risk_service already aggregates disease/weather/
    # task/financial signals into one score for this exact crop cycle
    # (Phase 33) - only surfaced when it says something worth a farmer's
    # attention (medium/high), never "low"/"insufficient_data" noise.
    if crop.get("available"):
        risk = crop_risk_service.get_risk_score(
            db, farmer_id, uuid.UUID(crop["crop_cycle_id"]), weather_provider=weather_provider, settings=settings
        )
        if risk.overall_risk in ("medium", "high"):
            priority = _LINE_PRIORITY["risk_high"] if risk.overall_risk == "high" else _LINE_PRIORITY["risk_medium"]
            scored_lines.append((priority, get_message("daily_summary_risk", language_code, level=risk.overall_risk)))

    # D92-08/D93-09: crop_financial_service already computes actual spend
    # for this crop cycle (Phase 31) - only surfaced once something has
    # actually been spent, consistent with every other line's "only
    # report what's actually there" discipline.
    if crop.get("available"):
        finance = crop_financial_service.get_financial_summary(db, farmer_id, uuid.UUID(crop["crop_cycle_id"]))
        if finance.actual_cost and finance.actual_cost > 0:
            scored_lines.append((_LINE_PRIORITY["finance"], get_message("daily_summary_finance", language_code, actual_cost=finance.actual_cost)))

    # D93-05 (docs/audit/FINAL_CANONICAL_group_D.md): irrigation_intelligence_service.py
    # already existed (Phase 38.4) and was never wired into the daily
    # brief - only surfaced when it says something actionable (never
    # NO_ACTION/UNKNOWN noise), same discipline as every other line here.
    if crop.get("available"):
        irrigation = tools.get_irrigation_status(db, farmer_id, weather_provider, settings)
        if irrigation.get("available") and irrigation["recommendation"] not in ("no_action", "unknown"):
            scored_lines.append((_LINE_PRIORITY["irrigation"], get_message("daily_summary_irrigation", language_code, reason=irrigation["reason"])))

    harvest = tools.get_harvest_status(db, farmer_id)
    if harvest.get("available") and harvest["status"] in ("approaching", "ready", "listed"):
        scored_lines.append((_LINE_PRIORITY["harvest"], get_message("daily_summary_harvest", language_code, status=harvest["status"])))

    offers = tools.get_buyer_offers(db, farmer_id)
    if offers.get("available") and offers["offer_count"] > 0:
        scored_lines.append((_LINE_PRIORITY["marketplace"], get_message("daily_summary_marketplace", language_code, offer_count=offers["offer_count"])))

    delivery = tools.get_delivery_status(db, farmer_id)
    if delivery.get("available") and delivery["status"] not in ("delivered",):
        scored_lines.append((_LINE_PRIORITY["delivery"], get_message("daily_summary_delivery", language_code, status=delivery["status"])))

    # Added Step 14: the tool already existed (Prompt 11/Step 13's
    # get_expert_case_status) but was never included in the daily
    # summary composition - a real, minimal gap closed by reusing it
    # exactly like every other line above, not by building anything new.
    case = tools.get_expert_case_status(db, farmer_id)
    if case.get("available") and case["status"] not in ("closed", "cancelled"):
        scored_lines.append((_LINE_PRIORITY["expert_review"], get_message("daily_summary_expert_review", language_code, status=case["status"])))

    # Added Step 16: reuses task_repository.list_overdue_for_farmer
    # directly (a simple count, not a farmer-question-answering tool, so
    # it doesn't need a new entry in tools.py's get_* function set) - the
    # same "only report what's actually there, no invented urgency"
    # discipline as every other line above.
    from app.repositories import task_repository

    overdue_tasks = task_repository.list_overdue_for_farmer(db, uuid.UUID(farmer_id), today=datetime.now(timezone.utc).date())
    overdue_count = len(overdue_tasks)
    if overdue_tasks:
        scored_lines.append((
            _LINE_PRIORITY["tasks_overdue"],
            get_message("daily_summary_tasks_overdue", language_code, count=overdue_count, plural="s" if overdue_count != 1 else ""),
        ))

    if not scored_lines:
        scored_lines.append((_LINE_PRIORITY["no_updates"], get_message("daily_summary_no_updates", language_code)))

    # D94-07 (docs/audit/FINAL_CANONICAL_group_D.md): order/payment status
    # was never pulled into the daily summary at all - reused here only
    # for the "what changed" comparison below, same tool chat already uses.
    order = tools.get_my_orders(db, farmer_id)

    # D94-08 (docs/FINAL_GAP_REPORT.md): a snapshot of the exact raw
    # facts feeding the lines above (never anything new), diffed against
    # the farmer's previous fetch to tell them what's changed since their
    # last visit - no new "events" table or diff engine, just this one
    # small stored snapshot, overwritten every time this is called.
    profile = getattr(user, "farmer_profile", None) if user else None
    if profile is not None:
        current_snapshot = _build_daily_summary_snapshot(
            weather=weather, crop=crop, disease=disease, risk=risk, finance=finance,
            harvest=harvest, offers=offers, delivery=delivery, case=case, overdue_count=overdue_count, order=order,
        )
        previous_snapshot = profile.last_daily_summary_snapshot
        previous_at = profile.last_daily_summary_at
        changed_since_banner: str | None = None
        if previous_snapshot is not None:
            changed_count = _count_changed_facts(previous_snapshot, current_snapshot)
            if changed_count > 0:
                changed_since_banner = get_message("daily_summary_changed_since_last_visit", language_code, count=changed_count)

            # D94-01/02/03/06/07: each is a distinct, named line on top of
            # the aggregate count above - only ever fires on a REAL
            # difference against the stored snapshot, never on the first
            # visit (previous_snapshot is None then, handled by the outer
            # `if`) and never fabricated when either side is unknown.
            if (
                weather.get("available") and previous_snapshot.get("weather_available")
                and (weather.get("current_temperature_c") != previous_snapshot.get("weather_temp")
                     or weather.get("rain_probability_today_percent") != previous_snapshot.get("weather_rain"))
            ):
                scored_lines.append((_LINE_PRIORITY["changed_detail"], get_message(
                    "daily_summary_weather_changed", language_code,
                    temp=weather.get("current_temperature_c", "?"), rain=weather.get("rain_probability_today_percent", "?"),
                )))

            new_stage = current_snapshot.get("crop_stage")
            if new_stage is not None and previous_snapshot.get("crop_stage") is not None and new_stage != previous_snapshot.get("crop_stage"):
                scored_lines.append((_LINE_PRIORITY["changed_detail"], get_message("daily_summary_stage_changed", language_code, stage=new_stage)))

            new_risk_level = current_snapshot.get("risk_level")
            if new_risk_level is not None and previous_snapshot.get("risk_level") is not None and new_risk_level != previous_snapshot.get("risk_level"):
                scored_lines.append((_LINE_PRIORITY["changed_detail"], get_message("daily_summary_risk_changed", language_code, level=new_risk_level)))

            new_review_outcome = current_snapshot.get("case_review_outcome")
            if new_review_outcome is not None and new_review_outcome != previous_snapshot.get("case_review_outcome"):
                scored_lines.append((_LINE_PRIORITY["changed_detail"], get_message("daily_summary_expert_responded", language_code)))

            # Unlike weather/stage/risk above, a None "previous" order status
            # here means "had no confirmed order yet" (list_orders_for_farmer
            # deliberately excludes DRAFT carts) - a farmer's first order
            # reaching a real status IS itself the meaningful payment event,
            # not an unknown-data case to suppress.
            new_order_status = current_snapshot.get("order_status")
            if new_order_status is not None and new_order_status != previous_snapshot.get("order_status"):
                scored_lines.append((_LINE_PRIORITY["changed_detail"], get_message("daily_summary_payment_changed", language_code, status=new_order_status)))

            # D94-04: a since-timestamp count, not a snapshot-diff (a
            # single stored "stage" string can't represent "how many
            # tasks changed" the way it can for weather/stage/risk).
            if previous_at is not None:
                completed_since = task_repository.count_completed_since(db, uuid.UUID(farmer_id), previous_at)
                created_since = task_repository.count_created_since(db, uuid.UUID(farmer_id), previous_at)
                if completed_since > 0 or created_since > 0:
                    scored_lines.append((
                        _LINE_PRIORITY["changed_detail"],
                        get_message("daily_summary_tasks_changed", language_code, completed=completed_since, created=created_since),
                    ))

        profile.last_daily_summary_snapshot = current_snapshot
        profile.last_daily_summary_at = datetime.now(timezone.utc)
        db.commit()

        # D92-09: stable sort (Python's own guarantee) - lines of equal
        # priority keep this function's own fixed composition order as a
        # tiebreak, so nothing reorders unless a genuine severity
        # difference calls for it. The "changed since last visit" banner
        # is a meta-summary of the count below it, not itself a single-
        # topic severity item - kept unconditionally first, exactly as
        # before this change.
        scored_lines.sort(key=lambda item: item[0], reverse=True)
        lines = [text for _, text in scored_lines]
        if changed_since_banner is not None:
            lines.insert(0, changed_since_banner)
    else:
        scored_lines.sort(key=lambda item: item[0], reverse=True)
        lines = [text for _, text in scored_lines]

    return DailySummaryResponse(language_code=language_code, lines=lines, generated_at=datetime.now(timezone.utc))


def _build_daily_summary_snapshot(*, weather, crop, disease, risk, finance, harvest, offers, delivery, case, overdue_count: int, order: dict) -> dict:
    """JSON-safe raw facts only - never the rendered/localized line text,
    so a farmer switching language never registers as a spurious change."""
    return {
        "weather_available": weather.get("available", False),
        "weather_temp": weather.get("current_temperature_c"),
        "weather_rain": weather.get("rain_probability_today_percent"),
        "crop_stage": crop.get("stage") if crop.get("available") else None,
        "disease_result_status": disease.get("result_status") if disease.get("available") else None,
        "risk_level": risk.overall_risk if risk is not None else None,
        "finance_actual_cost": str(finance.actual_cost) if finance is not None else None,
        "harvest_status": harvest.get("status") if harvest.get("available") else None,
        "offer_count": offers.get("offer_count") if offers.get("available") else None,
        "delivery_status": delivery.get("status") if delivery.get("available") else None,
        "case_status": case.get("status") if case.get("available") else None,
        # D94-06 (docs/audit/FINAL_CANONICAL_group_D.md): distinct from
        # case_status above - a case can stay "in_review" across two
        # visits while still gaining a NEW review outcome in between.
        "case_review_outcome": case.get("review_outcome") if case.get("available") else None,
        "overdue_count": overdue_count,
        # D94-07: order/payment status, pulled only for this comparison.
        "order_status": order.get("status") if order.get("available") else None,
    }


def _count_changed_facts(previous: dict, current: dict) -> int:
    keys = set(previous) | set(current)
    return sum(1 for key in keys if previous.get(key) != current.get(key))

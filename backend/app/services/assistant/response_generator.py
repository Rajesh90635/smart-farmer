"""
Response generator: turns a tool's structured output into farmer-friendly
text via the SAME template system already used for weather/notification
messages (app/core/farmer_messages.py) - never a free-form LLM
composition for any data-backed intent. If a tool reports
available: False, the response is ALWAYS an honest "I don't have that
information" - never a fabricated answer, enforced structurally here:
there is no code path that invents a value when a tool returns no data.
"""
from app.core.farmer_messages import get_message
from app.models.assistant_conversation import ConfidenceLevel
from app.services.assistant.intent_router import Intent


def generate_response(intent: Intent, tool_result: dict, language_code: str) -> tuple[str, ConfidenceLevel | None, list[str]]:
    """Returns (response_text, confidence, sources)."""
    sources = [tool_result["source"]] if tool_result.get("source") else []

    if intent == Intent.CROP_STATUS:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_crop", language_code), None, sources
        text = get_message("assistant_crop_status", language_code, crop_name=tool_result["crop_name"], farm_name=tool_result["farm_name"], stage=tool_result["stage"])
        return text, ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.DISEASE_STATUS:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_disease", language_code), None, sources
        status = tool_result["result_status"]
        if status == "healthy":
            return get_message("assistant_disease_healthy", language_code), ConfidenceLevel.HIGH_CONFIDENCE, sources
        if status == "disease_detected":
            level = {"high": ConfidenceLevel.HIGH_CONFIDENCE, "medium": ConfidenceLevel.MEDIUM_CONFIDENCE}.get(tool_result.get("confidence_level"), ConfidenceLevel.MEDIUM_CONFIDENCE)
            return get_message("assistant_disease_detected", language_code, predicted_class=tool_result["predicted_class"]), level, sources
        if status in ("low_confidence", "unknown", "crop_mismatch"):
            return get_message("assistant_disease_low_confidence", language_code), ConfidenceLevel.LOW_CONFIDENCE, sources
        return get_message("assistant_disease_unavailable", language_code), None, sources

    if intent == Intent.WEATHER:
        if not tool_result.get("source"):
            return get_message("assistant_no_data_weather", language_code), None, sources
        if not tool_result.get("available"):
            return get_message("assistant_weather_unavailable", language_code), None, sources
        prefix = get_message("assistant_weather_stale", language_code) if tool_result.get("is_stale") else ""
        text = prefix + get_message(
            "assistant_weather_summary", language_code,
            temp=tool_result.get("current_temperature_c", "?"), rain_prob=tool_result.get("rain_probability_today_percent", "?"),
        )
        return text, ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent in (Intent.HARVEST_READINESS, Intent.HARVEST_STATUS):
        if not tool_result.get("available"):
            return get_message("assistant_no_data_harvest", language_code), None, sources
        return get_message("assistant_harvest_status", language_code, status=tool_result["status"]), ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.BUYER_OFFER:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_offers", language_code), None, sources
        text = get_message("assistant_offers_summary", language_code, offer_count=tool_result["offer_count"], quantity=tool_result["listing_crop_quantity"], unit=tool_result["listing_unit"])
        return text, ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.MY_SALES:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_sales", language_code), None, sources
        latest_status = tool_result["recent_sales"][0]["status"] if tool_result["recent_sales"] else "unknown"
        text = get_message("assistant_sales_summary", language_code, total=tool_result["total_sales"], status=latest_status)
        return text, ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.MY_ORDERS:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_orders", language_code), None, sources
        return get_message("assistant_order_status", language_code, status=tool_result["status"]), ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.DELIVERY_STATUS:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_delivery", language_code), None, sources
        return get_message("assistant_delivery_status", language_code, status=tool_result["status"]), ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.EXPERT_CASE:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_expert_case", language_code), None, sources
        text = get_message("assistant_expert_case_status", language_code, status=tool_result["status"])
        if tool_result.get("review_outcome"):
            text += " " + get_message("assistant_expert_review_summary", language_code, outcome=tool_result["review_outcome"])
        return text, ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent in (Intent.FIND_SEED, Intent.PRICE_CHECK):
        if not tool_result.get("available"):
            return get_message("assistant_no_data_seeds", language_code), None, sources
        return get_message("assistant_seeds_summary", language_code, count=len(tool_result.get("products", []))), ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.SELL_CROP:
        if not tool_result.get("available"):
            return get_message("assistant_no_data_harvest", language_code), None, sources
        return get_message("assistant_harvest_status", language_code, status=tool_result.get("status", "unknown")), ConfidenceLevel.HIGH_CONFIDENCE, sources

    if intent == Intent.HELP:
        return get_message("assistant_help", language_code), ConfidenceLevel.HIGH_CONFIDENCE, []

    # GENERAL_AGRICULTURE and anything unimplemented - never fabricated.
    return get_message("assistant_general_unavailable", language_code), None, []

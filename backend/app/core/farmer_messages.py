"""
Farmer-friendly message templates. Structured templates per
(message_key, language_code), never raw AI/technical text shown directly
to a farmer. Fallback chain: farmer's preferred language -> English -> a
hardcoded safe default (never an empty notification).

Only English is fully populated this phase - Kannada/Telugu/Hindi/Tamil/
Malayalam/Marathi entries are intentionally left for native-speaker
review before being trusted for real farmer-facing text (auto-translating
agricultural/safety content without review would be worse than showing
English with a clear fallback). See docs/LOCALIZATION.md.
"""
from app.core.localization import DEFAULT_LANGUAGE_CODE

_TEMPLATES: dict[str, dict[str, str]] = {
    "ai_result_healthy": {"en": "Your {crop_name} crop looks healthy based on this photo."},
    "ai_result_disease_detected": {"en": "Possible {disease_name} detected in your {crop_name}."},
    "ai_result_unknown": {"en": "We could not identify the problem clearly. Please take a clearer photo."},
    "ai_result_low_confidence": {"en": "Unable to identify the problem confidently. Please take a clearer photo."},
    "ai_result_crop_mismatch": {"en": "This photo doesn't seem to match the crop you selected. Please check and try again."},
    "ai_result_ai_unavailable": {"en": "We couldn't check the photo right now. Please try again later."},
    "ai_result_failed": {"en": "Something went wrong while checking your photo. Please try again."},
    "ai_next_action_retake": {"en": "Take another clear photo if the result is uncertain."},
    "ai_next_action_review": {"en": "This result may need expert verification."},
    "rain_alert": {"en": "Rain is likely in your area today."},
    "heavy_rain_alert": {"en": "Heavier rain is expected. Plan farm work accordingly."},
    "high_wind_alert": {"en": "Strong winds are expected in your area."},
    "extreme_heat_alert": {"en": "Very high temperatures are expected today."},
    "extreme_cold_alert": {"en": "Unusually cold temperatures are expected today."},
    "crop_weather_heavy_rain": {"en": "Heavy rain is expected. Your {crop_name} is currently in the {stage} stage. Monitor the crop after rainfall."},
    "spray_condition_warning": {"en": "Weather conditions may not be suitable for spraying right now."},
    "weather_unavailable": {"en": "Weather information is temporarily unavailable."},
    "weather_stale": {"en": "Showing the last available weather update."},
    "CASE_CREATED": {"en": "Your request for professional help has been received."},
    "CASE_ASSIGNED": {"en": "A verified professional has been assigned to your case."},
    "CASE_ACCEPTED": {"en": "The professional has accepted your case and will review it soon."},
    "CASE_DECLINED": {"en": "We're finding another professional for your case."},
    "CASE_REASSIGNED": {"en": "Your case has been assigned to another available professional."},
    "CASE_REVIEWED": {"en": "Your case has been reviewed. Open the case to see the result."},
    "CASE_NEEDS_INFORMATION": {"en": "The professional needs more information or a clearer photo for your case."},
    "CASE_ESCALATED": {"en": "Your case has been escalated for further attention."},
    "CASE_CLOSED": {"en": "Your case has been closed."},
    "assistant_no_data_crop": {"en": "I don't have a current active crop record for you yet. Add a crop cycle to get started."},
    "assistant_crop_status": {"en": "Your {crop_name} on {farm_name} is currently at the {stage} stage."},
    "assistant_no_data_treatment": {"en": "No treatment has been recorded for this crop yet."},
    "assistant_treatment_no_follow_up": {"en": "You applied a treatment on {application_date}. No follow-up has been recorded yet."},
    "assistant_treatment_effectiveness": {"en": "You applied a treatment on {application_date}. Latest follow-up: {effectiveness_summary}"},
    "assistant_no_data_financial": {"en": "No cost or spending information has been recorded for this crop yet."},
    "assistant_financial_summary": {"en": "You've spent {actual_cost} so far on this crop. {estimate_note}"},
    "assistant_no_data_disease": {"en": "You have no crop photo analysis on record yet. Take a photo of your crop to check it."},
    "assistant_disease_healthy": {"en": "Your last photo check showed your crop looks healthy."},
    "assistant_disease_detected": {"en": "Your last photo check found a possible {predicted_class}. This is an AI observation, not a confirmed diagnosis."},
    "assistant_disease_low_confidence": {"en": "Your last photo check could not identify the issue confidently. Please take another clear photo or ask an expert."},
    "assistant_disease_unavailable": {"en": "We couldn't check your last photo - please try uploading it again."},
    "assistant_no_data_weather": {"en": "I don't have a farm with a location set up yet, so I can't check weather for you."},
    "assistant_weather_unavailable": {"en": "Weather information is temporarily unavailable right now."},
    "assistant_weather_stale": {"en": "Here is the last available weather update, which may not be current: "},
    "assistant_weather_summary": {"en": "It's currently {temp}°C, with a {rain_prob}% chance of rain today."},
    "assistant_no_data_harvest": {"en": "I don't have a harvest record for you yet."},
    "assistant_harvest_status": {"en": "Your harvest status is currently: {status}."},
    "assistant_no_data_offers": {"en": "You don't have any active harvest listings with offers right now."},
    "assistant_offers_summary": {"en": "You have {offer_count} active offer(s) on your listing of {quantity} {unit}."},
    "assistant_no_data_sales": {"en": "You haven't recorded any sales yet."},
    "assistant_sales_summary": {"en": "You have {total} sale(s) on record. Your most recent sale is currently: {status}."},
    "assistant_no_data_orders": {"en": "You don't have any orders on record yet."},
    "assistant_order_status": {"en": "Your most recent order is currently: {status}."},
    "assistant_no_data_delivery": {"en": "I don't have delivery information for you yet."},
    "assistant_delivery_status": {"en": "Your delivery status is: {status}."},
    "assistant_no_data_expert_case": {"en": "You don't have any expert case on record yet."},
    "assistant_expert_case_status": {"en": "Your expert case is currently: {status}."},
    "assistant_expert_review_summary": {"en": "The reviewer's assessment was: {outcome}."},
    "assistant_no_data_seeds": {"en": "I couldn't find any approved seed products matching that right now."},
    "assistant_seeds_summary": {"en": "I found {count} approved seed product(s) you can review and purchase."},
    "assistant_prescription_redirect": {"en": "I can't recommend a specific pesticide, fungicide, or dosage. This needs verified agricultural guidance - I can help you send this to an agriculture expert instead."},
    "assistant_general_unavailable": {"en": "I don't have enough information to answer that reliably. Please ask about your crop, weather, orders, or marketplace, or contact an agriculture expert for general guidance."},
    "assistant_help": {"en": "You can ask me about your crop, disease results, weather, harvest, buyer offers, your sales, your orders, deliveries, expert cases, or where to find seeds."},
}


def get_message(message_key: str, language_code: str, **params) -> str:
    """Returns the rendered message for (message_key, language_code),
    falling back to English, then to a safe generic string - never an
    empty or missing notification."""
    templates = _TEMPLATES.get(message_key)
    if templates is None:
        return "You have a new update."

    template = templates.get(language_code) or templates.get(DEFAULT_LANGUAGE_CODE)
    if template is None:
        return "You have a new update."

    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template

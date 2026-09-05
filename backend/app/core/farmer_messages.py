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
    "CASE_ASSIGNMENT_REMINDER": {"en": "A crop health case assigned to you is awaiting your response."},
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

    # --- Daily Briefing (Today's Briefing screen), keys below only ---
    # DRAFT, UNREVIEWED machine translations - explicitly requested by the
    # user to unblock location-based audio language switching, as an
    # exception to this file's normal English-only default. NOT
    # native-speaker-verified. Unlike every other entry above, these six
    # languages are populated - but flagged here, and in
    # docs/LOCALIZATION.md, as needing native-speaker review before being
    # trusted for real farmer-facing weather/crop content, per this file's
    # own stated rule (see module docstring) that a wrong translation of
    # exactly this kind of content is actively harmful. Do not copy this
    # pattern to any other key without the same explicit user sign-off.
    "daily_summary_weather": {
        "en": "Weather: {temp}°C, {rain}% chance of rain today.",
        "hi": "मौसम: आज {temp}°C, बारिश की {rain}% संभावना।",
        "te": "వాతావరణం: ఈరోజు {temp}°C, వర్షం పడే అవకాశం {rain}%.",
        "ta": "வானிலை: இன்று {temp}°C, மழை பெய்யும் வாய்ப்பு {rain}%.",
        "kn": "ಹವಾಮಾನ: ಇಂದು {temp}°C, ಮಳೆಯ ಸಾಧ್ಯತೆ {rain}%.",
        "ml": "കാലാവസ്ഥ: ഇന്ന് {temp}°C, മഴയ്ക്കുള്ള സാധ്യത {rain}%.",
        "mr": "हवामान: आज {temp}°C, पावसाची शक्यता {rain}%.",
    },
    "daily_summary_crop": {
        "en": "Crop: your {crop_name} is at the {stage} stage.",
        "hi": "फसल: आपकी {crop_name} अभी {stage} चरण में है।",
        "te": "పంట: మీ {crop_name} ప్రస్తుతం {stage} దశలో ఉంది.",
        "ta": "பயிர்: உங்கள் {crop_name} தற்போது {stage} நிலையில் உள்ளது.",
        "kn": "ಬೆಳೆ: ನಿಮ್ಮ {crop_name} ಪ್ರಸ್ತುತ {stage} ಹಂತದಲ್ಲಿದೆ.",
        "ml": "വിള: നിങ്ങളുടെ {crop_name} ഇപ്പോൾ {stage} ഘട്ടത്തിലാണ്.",
        "mr": "पीक: तुमचे {crop_name} सध्या {stage} अवस्थेत आहे.",
    },
    "daily_summary_risk": {
        "en": "Risk: your crop's overall risk level is currently {level}.",
        "hi": "जोखिम: आपकी फसल का समग्र जोखिम स्तर वर्तमान में {level} है।",
        "te": "ప్రమాదం: మీ పంట మొత్తం ప్రమాద స్థాయి ప్రస్తుతం {level}గా ఉంది.",
        "ta": "ஆபத்து: உங்கள் பயிரின் ஒட்டுமொத்த ஆபத்து நிலை தற்போது {level} ஆக உள்ளது.",
        "kn": "ಅಪಾಯ: ನಿಮ್ಮ ಬೆಳೆಯ ಒಟ್ಟಾರೆ ಅಪಾಯದ ಮಟ್ಟ ಪ್ರಸ್ತುತ {level} ಆಗಿದೆ.",
        "ml": "അപകടസാധ്യത: നിങ്ങളുടെ വിളയുടെ മൊത്തത്തിലുള്ള അപകടസാധ്യതാ നില നിലവിൽ {level} ആണ്.",
        "mr": "जोखीम: तुमच्या पिकाची एकूण जोखीम पातळी सध्या {level} आहे.",
    },
    "daily_summary_disease": {
        "en": "Health check: a possible {predicted_class} was detected in your last photo check.",
        "hi": "स्वास्थ्य जांच: आपकी पिछली फोटो जांच में संभावित {predicted_class} पाया गया।",
        "te": "ఆరోగ్య పరిశీలన: మీ చివరి ఫోటో పరిశీలనలో {predicted_class} అవకాశం కనుగొనబడింది.",
        "ta": "சுகாதார சோதனை: உங்கள் கடைசி புகைப்பட சோதனையில் சாத்தியமான {predicted_class} கண்டறியப்பட்டது.",
        "kn": "ಆರೋಗ್ಯ ತಪಾಸಣೆ: ನಿಮ್ಮ ಕೊನೆಯ ಫೋಟೋ ಪರಿಶೀಲನೆಯಲ್ಲಿ ಸಂಭಾವ್ಯ {predicted_class} ಪತ್ತೆಯಾಗಿದೆ.",
        "ml": "ആരോഗ്യ പരിശോധന: നിങ്ങളുടെ അവസാന ഫോട്ടോ പരിശോധനയിൽ സാധ്യതയുള്ള {predicted_class} കണ്ടെത്തി.",
        "mr": "आरोग्य तपासणी: तुमच्या शेवटच्या फोटो तपासणीत संभाव्य {predicted_class} आढळले.",
    },
    "daily_summary_finance": {
        "en": "Expenses: you've spent {actual_cost} so far on this crop.",
        "hi": "खर्च: आपने इस फसल पर अब तक {actual_cost} खर्च किए हैं।",
        "te": "ఖర్చులు: మీరు ఈ పంటపై ఇప్పటివరకు {actual_cost} ఖర్చు చేశారు.",
        "ta": "செலவுகள்: இந்த பயிருக்கு நீங்கள் இதுவரை {actual_cost} செலவிட்டுள்ளீர்கள்.",
        "kn": "ವೆಚ್ಚಗಳು: ಈ ಬೆಳೆಗಾಗಿ ನೀವು ಇಲ್ಲಿಯವರೆಗೆ {actual_cost} ಖರ್ಚು ಮಾಡಿದ್ದೀರಿ.",
        "ml": "ചെലവുകൾ: ഈ വിളയ്ക്കായി നിങ്ങൾ ഇതുവരെ {actual_cost} ചെലവഴിച്ചു.",
        "mr": "खर्च: या पिकावर तुम्ही आतापर्यंत {actual_cost} खर्च केले आहेत.",
    },
    "daily_summary_harvest": {
        "en": "Harvest: currently {status}.",
        "hi": "कटाई: वर्तमान स्थिति {status}।",
        "te": "పంట కోత: ప్రస్తుత స్థితి {status}.",
        "ta": "அறுவடை: தற்போதைய நிலை {status}.",
        "kn": "ಕೊಯ್ಲು: ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ {status}.",
        "ml": "വിളവെടുപ്പ്: നിലവിലെ അവസ്ഥ {status}.",
        "mr": "कापणी: सध्याची स्थिती {status}.",
    },
    "daily_summary_marketplace": {
        "en": "Marketplace: {offer_count} buyer offer(s) on your current listing.",
        "hi": "बाज़ार: आपकी सूची पर {offer_count} खरीदार प्रस्ताव।",
        "te": "మార్కెట్‌ప్లేస్: మీ లిస్టింగ్‌పై {offer_count} కొనుగోలుదారు ఆఫర్లు.",
        "ta": "சந்தை: உங்கள் பட்டியலில் {offer_count} வாங்குபவர் சலுகைகள்.",
        "kn": "ಮಾರುಕಟ್ಟೆ: ನಿಮ್ಮ ಪಟ್ಟಿಯಲ್ಲಿ {offer_count} ಖರೀದಿದಾರರ ಕೊಡುಗೆಗಳು.",
        "ml": "മാർക്കറ്റ്: നിങ്ങളുടെ ലിസ്റ്റിംഗിൽ {offer_count} വാങ്ങുന്നവരുടെ ഓഫറുകൾ.",
        "mr": "बाजारपेठ: तुमच्या यादीवर {offer_count} खरेदीदार ऑफर्स.",
    },
    "daily_summary_delivery": {
        "en": "Delivery: your order is currently {status}.",
        "hi": "डिलीवरी: आपका ऑर्डर वर्तमान में {status} है।",
        "te": "డెలివరీ: మీ ఆర్డర్ ప్రస్తుతం {status}.",
        "ta": "விநியோகம்: உங்கள் ஆர்டர் தற்போது {status}.",
        "kn": "ವಿತರಣೆ: ನಿಮ್ಮ ಆರ್ಡರ್ ಪ್ರಸ್ತುತ {status}.",
        "ml": "ഡെലിവറി: നിങ്ങളുടെ ഓർഡർ നിലവിൽ {status}.",
        "mr": "डिलिव्हरी: तुमची ऑर्डर सध्या {status} आहे.",
    },
    "daily_summary_expert_review": {
        "en": "Expert review: your case is currently {status}.",
        "hi": "विशेषज्ञ समीक्षा: आपका मामला वर्तमान में {status} है।",
        "te": "నిపుణుల సమీక్ష: మీ కేసు ప్రస్తుతం {status}.",
        "ta": "நிபுணர் மதிப்பாய்வு: உங்கள் வழக்கு தற்போது {status}.",
        "kn": "ತಜ್ಞರ ಪರಿಶೀಲನೆ: ನಿಮ್ಮ ಪ್ರಕರಣ ಪ್ರಸ್ತುತ {status}.",
        "ml": "വിദഗ്ദ്ധ അവലോകനം: നിങ്ങളുടെ കേസ് നിലവിൽ {status}.",
        "mr": "तज्ञ पुनरावलोकन: तुमचे प्रकरण सध्या {status} आहे.",
    },
    "daily_summary_tasks_overdue": {
        "en": "Tasks: you have {count} overdue task{plural}.",
        "hi": "कार्य: आपके पास {count} विलंबित कार्य हैं।",
        "te": "పనులు: మీకు {count} ఆలస్యమైన పనులు ఉన్నాయి.",
        "ta": "பணிகள்: உங்களிடம் {count} தாமதமான பணிகள் உள்ளன.",
        "kn": "ಕಾರ್ಯಗಳು: ನಿಮಗೆ {count} ವಿಳಂಬವಾದ ಕಾರ್ಯಗಳಿವೆ.",
        "ml": "ജോലികൾ: നിങ്ങൾക്ക് {count} കാലതാമസം വന്ന ജോലികൾ ഉണ്ട്.",
        "mr": "कामे: तुमच्याकडे {count} विलंबित कामे आहेत.",
    },
    "daily_summary_no_updates": {
        "en": "No new updates for your farm right now.",
        "hi": "अभी आपके खेत के लिए कोई नई जानकारी नहीं है।",
        "te": "మీ పొలం కోసం ప్రస్తుతం కొత్త అప్‌డేట్‌లు లేవు.",
        "ta": "இப்போது உங்கள் பண்ணைக்கு புதிய புதுப்பிப்புகள் இல்லை.",
        "kn": "ಸದ್ಯಕ್ಕೆ ನಿಮ್ಮ ಜಮೀನಿಗೆ ಯಾವುದೇ ಹೊಸ ಅಪ್‌ಡೇಟ್‌ಗಳಿಲ್ಲ.",
        "ml": "നിലവിൽ നിങ്ങളുടെ കൃഷിയിടത്തിന് പുതിയ അപ്ഡേറ്റുകൾ ഇല്ല.",
        "mr": "सध्या तुमच्या शेतासाठी कोणतीही नवीन माहिती नाही.",
    },
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

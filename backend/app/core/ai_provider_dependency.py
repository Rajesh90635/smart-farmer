"""
Single switch point for the assistant's AIProvider - mirrors
get_model_provider (Prompt 6) and get_weather_provider (Prompt 7)
exactly. No API key is configured in Settings this phase, so this always
returns NotConfiguredAIProvider - see docs/AI_MODEL_PROVIDER.md.
"""
from functools import lru_cache

from app.services.assistant.ai_provider import AIProvider
from app.services.assistant.not_configured_provider import NotConfiguredAIProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    return NotConfiguredAIProvider()

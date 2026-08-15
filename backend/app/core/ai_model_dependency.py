"""
FastAPI dependency providing the configured ModelProvider. Exactly one
production implementation exists this phase: NotConfiguredModelProvider.
Swapping in a real model later means changing this one function - no
endpoint or service code needs to change.
"""
from functools import lru_cache

from app.services.ai.model_provider import ModelProvider
from app.services.ai.not_configured_provider import NotConfiguredModelProvider


@lru_cache
def get_model_provider() -> ModelProvider:
    return NotConfiguredModelProvider()

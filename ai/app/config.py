from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "smart-farmer-ai"
    environment: Literal["development", "testing", "production"] = "development"

    # Which model provider backs each capability. "none" means the
    # foundation abstraction exists but no real model is wired in yet -
    # correct value for this phase per the Do-Not-Implement-Yet rule.
    vision_provider: Literal["none", "local_open_model", "huggingface"] = "none"
    llm_provider: Literal["none", "ollama", "claude_api"] = "none"


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()

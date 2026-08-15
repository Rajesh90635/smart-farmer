"""
Smart Farmer AI service — foundation only.

Per Step 7 of the spec: no disease-detection model is implemented here.
This exposes GET /ai/health, reporting whether each capability's model
provider is ready (always "not ready" in this phase, since every provider
is NotImplementedModelProvider by design).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_ai_settings
from app.logging_config import configure_logging, get_logger
from app.model_abstraction import InferenceService, NotImplementedModelProvider

settings = get_ai_settings()
logger = get_logger(__name__)

vision_service = InferenceService(NotImplementedModelProvider("crop_disease_vision"))
llm_service = InferenceService(NotImplementedModelProvider("llm_explanation"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")
    logger.info("Starting %s (vision_provider=%s, llm_provider=%s)",
                settings.service_name, settings.vision_provider, settings.llm_provider)
    yield
    logger.info("Shutting down %s", settings.service_name)


app = FastAPI(
    title="Smart Farmer AI Service",
    version="0.1.0",
    description="Foundation build - no models implemented yet. See PROJECT_STATUS.md.",
    lifespan=lifespan,
)


@app.get("/ai/health")
def ai_health() -> dict:
    return {
        "status": "healthy",
        "capabilities": {
            "vision": vision_service.health(),
            "llm": llm_service.health(),
        },
    }

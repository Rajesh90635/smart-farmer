"""
NotConfiguredModelProvider: the ONLY ModelProvider wired into production
this phase (see app/api/v1/ai_dependencies.py). No real disease-detection
or crop-stage model has been trained, selected, or integrated - see
docs/AI_ARCHITECTURE.md for the evaluation of candidate approaches and why
none was integrated yet (network restrictions in the dev environment
prevented downloading any candidate model/dataset this phase, in addition
to the deliberate "do not train a huge model yet" instruction).

This class NEVER fabricates a prediction. Every method honestly reports
`available=False` - this is what makes AIAnalysis.result_status =
AI_UNAVAILABLE (Requirement 36) the true, correct outcome for every real
analysis request in this phase, not a bug or a placeholder someone forgot
to finish.
"""
from app.services.ai.model_provider import DiseasePrediction, ModelProvider, StagePrediction


class NotConfiguredModelProvider(ModelProvider):
    _UNAVAILABLE_REASON = "No AI model is configured in this environment yet."

    @property
    def model_name(self) -> str:
        return "crop_disease_baseline"

    @property
    def model_version(self) -> str:
        return "unconfigured-0.0"

    def is_ready(self) -> bool:
        return False

    def supported_crop_names(self) -> list[str]:
        return []

    def predict_disease(self, image_bytes: bytes, crop_name: str) -> DiseasePrediction:
        return DiseasePrediction(available=False, unavailable_reason=self._UNAVAILABLE_REASON)

    def predict_stage(self, image_bytes: bytes, crop_name: str) -> StagePrediction:
        return StagePrediction(available=False, unavailable_reason=self._UNAVAILABLE_REASON)

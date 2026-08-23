"""
FakeModelProvider - TEST-ONLY. Never imported by any app/ production code
- only used here, injected via FastAPI's dependency_overrides, to exercise
the safety-layer logic (confidence thresholds, unknown/crop-mismatch
handling, healthy/disease mapping) with controlled, known inputs. The
production default (see app/core/ai_model_dependency.py) remains
NotConfiguredModelProvider for every real farmer-facing request - this
class's existence does not violate the "no fake AI" rule since it can
never run in response to an actual farmer's photo.
"""
from app.services.ai.model_provider import DiseasePrediction, ModelProvider, StagePrediction, TopKPrediction


class FakeModelProvider(ModelProvider):
    def __init__(
        self,
        *,
        ready: bool = True,
        supported_crops: list[str] | None = None,
        top_predictions: list[TopKPrediction] | None = None,
        crop_match: bool | None = True,
        raise_on_predict: bool = False,
    ):
        self._ready = ready
        self._supported_crops = supported_crops if supported_crops is not None else ["tomato"]
        self._top_predictions = top_predictions if top_predictions is not None else [TopKPrediction("Early Blight", 0.92)]
        self._crop_match = crop_match
        self._raise_on_predict = raise_on_predict

    @property
    def model_name(self) -> str:
        return "fake_test_model"

    @property
    def model_version(self) -> str:
        return "test-1.0"

    def is_ready(self) -> bool:
        return self._ready

    def supported_crop_names(self) -> list[str]:
        return self._supported_crops

    def predict_disease(self, image_bytes: bytes, crop_name: str) -> DiseasePrediction:
        if self._raise_on_predict:
            raise RuntimeError("Simulated model failure for testing.")
        if not self._ready:
            return DiseasePrediction(available=False, unavailable_reason="fake provider marked not ready")
        return DiseasePrediction(available=True, top_predictions=self._top_predictions, crop_match=self._crop_match)

    def predict_stage(self, image_bytes: bytes, crop_name: str) -> StagePrediction:
        return StagePrediction(available=False, unavailable_reason="stage prediction not exercised by this fake")

"""
ModelProvider: the abstraction every AI model implementation sits behind.
Business/API code depends on this interface, never on a specific model or
framework - swapping TensorFlow for PyTorch for ONNX Runtime for a
HTTP call to the separate `ai/` service means writing one new class here,
not touching any endpoint or service that calls it.

Every method returns a result object with `available: bool` rather than
raising - "the model isn't ready" is an expected, safety-relevant outcome
the caller must handle explicitly (route to AI_UNAVAILABLE), not an
exception path that might get silently swallowed somewhere.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TopKPrediction:
    class_name: str
    confidence: float


@dataclass(frozen=True)
class DiseasePrediction:
    available: bool
    top_predictions: list[TopKPrediction] = field(default_factory=list)
    # None = the model has no crop-identification capability at all, so no
    # opinion is offered on match/mismatch (not the same as "matched").
    crop_match: bool | None = None
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class StagePrediction:
    available: bool
    stage_code: str | None = None
    confidence: float | None = None
    unavailable_reason: str | None = None


class ModelProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @abstractmethod
    def is_ready(self) -> bool: ...

    @abstractmethod
    def supported_crop_names(self) -> list[str]:
        """Lowercase crop names this model can actually recognize. An
        empty list is honest and expected when no model is configured -
        callers must never assume a crop is supported just because it
        exists in CropMaster."""

    @abstractmethod
    def predict_disease(self, image_bytes: bytes, crop_name: str) -> DiseasePrediction: ...

    @abstractmethod
    def predict_stage(self, image_bytes: bytes, crop_name: str) -> StagePrediction: ...

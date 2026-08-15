"""
AI service abstraction layer.

These interfaces exist so business logic in the backend (once the disease-
diagnosis module is built) calls a stable contract, never a specific model
or provider directly. Swapping "a small local open-source classifier" for
"a Hugging Face-hosted model" for "a future commercial API" happens by
implementing a new ModelProvider and changing configuration - not by
touching any caller.

Per the current phase's rules, NO real model is implemented here. Calling
NotImplementedModelProvider raises clearly rather than silently returning a
fabricated result - a model that doesn't exist yet must never pretend to.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelVersion:
    provider: str
    name: str
    version: str


@dataclass(frozen=True)
class InferenceResult:
    """Generic shape for any classifier-style result. The disease-diagnosis
    module will define a more specific result type when it's implemented;
    this is intentionally generic so the abstraction isn't coupled to a
    feature that doesn't exist yet."""

    candidate_label: str
    confidence: float
    model_version: ModelVersion


class ModelProvider(ABC):
    """A ModelProvider knows how to run inference for one capability
    (e.g. crop-disease classification) using one specific backing model."""

    @property
    @abstractmethod
    def model_version(self) -> ModelVersion:
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the underlying model is loaded and able to serve
        requests. The health endpoint reports this per-provider."""

    @abstractmethod
    def predict(self, input_bytes: bytes) -> InferenceResult:
        ...


class NotImplementedModelProvider(ModelProvider):
    """Explicit placeholder used while `vision_provider`/`llm_provider` is
    "none". Never silently returns a fabricated confidence - raises instead,
    so a caller can't accidentally treat "not built yet" as "diagnosed"."""

    def __init__(self, capability_name: str):
        self._capability_name = capability_name

    @property
    def model_version(self) -> ModelVersion:
        return ModelVersion(provider="none", name=self._capability_name, version="unimplemented")

    def is_ready(self) -> bool:
        return False

    def predict(self, input_bytes: bytes) -> InferenceResult:
        raise NotImplementedError(
            f"'{self._capability_name}' has no model wired in yet - this is expected in the "
            "foundation phase. See PROJECT_STATUS.md for which phase implements it."
        )


class InferenceService:
    """Thin orchestration layer the API routes call. Exists mainly so
    request handling (validation, error shaping) is separated from model
    selection - a repeated pattern from the backend foundation, applied
    here too."""

    def __init__(self, provider: ModelProvider):
        self._provider = provider

    def health(self) -> dict:
        return {
            "ready": self._provider.is_ready(),
            "model": {
                "provider": self._provider.model_version.provider,
                "name": self._provider.model_version.name,
                "version": self._provider.model_version.version,
            },
        }

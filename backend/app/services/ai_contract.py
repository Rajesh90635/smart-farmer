"""
Future AI contract (Requirement 31).

CropPhoto -> ImageQualityService -> AIInferenceService -> DiseaseAnalysis

This phase implements the interface only. AIInferenceService.analyze()
returns a NOT_IMPLEMENTED result - it never fabricates a disease result,
confidence score, or any agricultural claim. It is NOT called from any
endpoint in this phase (see docs/CROP_PHOTO_MODULE.md) - wiring it into
the upload flow is deferred to the disease-detection epic, at which point
this same interface will either call the separate `ai/` FastAPI service
over HTTP or a local model, without the crop-photo upload code needing to
change.
"""
import enum
from dataclasses import dataclass


class AIAnalysisStatus(str, enum.Enum):
    NOT_IMPLEMENTED = "not_implemented"


@dataclass(frozen=True)
class AIAnalysisResult:
    status: AIAnalysisStatus
    detail: str


class AIInferenceService:
    def analyze(self, *, photo_id: str) -> AIAnalysisResult:
        return AIAnalysisResult(
            status=AIAnalysisStatus.NOT_IMPLEMENTED,
            detail="Disease analysis is not implemented in this phase.",
        )

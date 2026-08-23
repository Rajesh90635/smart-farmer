"""
AIProvider: the abstraction for the ONE piece of this assistant that would
genuinely benefit from a real generative model - open-ended
GENERAL_AGRICULTURE questions that don't map to a specific data-backed
intent. Every other intent (crop status, weather, orders, etc.) is
answered by the deterministic intent router + real tool calls + templated
responses - never by this provider - so a farmer never gets a fabricated
price, order status, or diagnosis regardless of whether this provider is
configured.

HONESTY NOTE: this environment has NO API key configured for any LLM
provider. Verified directly: api.anthropic.com is network-reachable from
this sandbox, but a real request without a key correctly returns
authentication_error: x-api-key header is required - confirming no key
is available here, not just untested. NotConfiguredAIProvider is
therefore the only provider actually used in this build - see
docs/AI_MODEL_PROVIDER.md.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneralQuestionResult:
    available: bool
    answer: str | None = None
    unavailable_reason: str | None = None


class AIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def is_ready(self) -> bool: ...

    @abstractmethod
    def answer_general_question(self, question: str, *, language_code: str) -> GeneralQuestionResult:
        """Only ever called for GENERAL_AGRICULTURE intent - never for any
        intent that has a real data-backed tool available."""

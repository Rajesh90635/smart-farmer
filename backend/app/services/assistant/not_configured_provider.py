from app.services.assistant.ai_provider import AIProvider, GeneralQuestionResult


class NotConfiguredAIProvider(AIProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    def is_ready(self) -> bool:
        return False

    def answer_general_question(self, question: str, *, language_code: str) -> GeneralQuestionResult:
        return GeneralQuestionResult(available=False, unavailable_reason="No AI provider is configured in this environment.")

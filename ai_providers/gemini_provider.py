from __future__ import annotations

from ai_providers.base_provider import AIResult, BaseAIProvider
from config import get_settings


class GeminiProvider(BaseAIProvider):
    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        super().__init__(model_name=model_name or settings.gemini_model)
        self._client = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    def initialize(self) -> bool:
        if not self.api_key:
            return False
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model_name)
            self._initialized = True
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return bool(self._initialized and self._client)

    def generate(self, prompt: str, system_prompt: str | None = None) -> AIResult:
        if not self._initialized and not self.initialize():
            return AIResult(success=False, error="Gemini is not configured.")
        try:
            final_prompt = prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
            resp = self._client.generate_content(final_prompt)
            text = getattr(resp, "text", "") or ""
            return AIResult(success=True, text=text)
        except Exception as exc:
            return AIResult(success=False, error=str(exc))

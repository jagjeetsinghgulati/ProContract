from __future__ import annotations

from ai_providers.base_provider import BaseAIProvider, ProviderType
from ai_providers.gemini_provider import GeminiProvider
from ai_providers.lmstudio_provider import LMStudioProvider, check_lmstudio_status
from ai_providers.ollama_provider import OllamaProvider, check_ollama_status
from config import get_settings


class ProviderFactory:
    def __init__(self) -> None:
        self._cache: dict[str, BaseAIProvider] = {}

    def get_provider(
        self,
        provider_type: ProviderType | str | None = None,
        allow_cloud: bool = False,
    ) -> BaseAIProvider | None:
        settings = get_settings()
        normalized = (provider_type or settings.default_provider or "none").lower()

        if normalized == ProviderType.NONE.value:
            return None

        if normalized == ProviderType.GEMINI.value and not allow_cloud:
            return None

        provider = self._cache.get(normalized)
        if not provider:
            provider = self._create_provider(normalized)
            if provider:
                self._cache[normalized] = provider
        if provider and provider.initialize() and provider.is_available():
            return provider
        return None

    def _create_provider(self, provider_type: str) -> BaseAIProvider | None:
        if provider_type == ProviderType.OLLAMA.value:
            return OllamaProvider()
        if provider_type == ProviderType.LMSTUDIO.value:
            return LMStudioProvider()
        if provider_type == ProviderType.GEMINI.value:
            return GeminiProvider()
        return None

    def check_status(self) -> dict:
        status = {
            "ollama": check_ollama_status(),
            "lmstudio": check_lmstudio_status(),
            "gemini": {"running": bool(GeminiProvider().initialize()), "models": []},
        }
        recommended = "none"
        if status["ollama"]["running"]:
            recommended = "ollama"
        elif status["lmstudio"]["running"]:
            recommended = "lmstudio"
        elif status["gemini"]["running"]:
            recommended = "gemini"
        status["recommended"] = recommended
        return status


_factory: ProviderFactory | None = None


def get_factory() -> ProviderFactory:
    global _factory
    if _factory is None:
        _factory = ProviderFactory()
    return _factory

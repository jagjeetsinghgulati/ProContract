from __future__ import annotations

import requests

from ai_providers.base_provider import AIResult, BaseAIProvider
from config import get_settings


class OllamaProvider(BaseAIProvider):
    def __init__(self, model_name: str | None = None, host: str | None = None):
        settings = get_settings()
        self.host = host or settings.ollama_host
        super().__init__(model_name=model_name or settings.ollama_model)

    @property
    def provider_name(self) -> str:
        return "ollama"

    def initialize(self) -> bool:
        self._initialized = self.is_available()
        return self._initialized

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate(self, prompt: str, system_prompt: str | None = None) -> AIResult:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            response = requests.post(f"{self.host}/api/generate", json=payload, timeout=60)
            response.raise_for_status()
            body = response.json()
            return AIResult(success=True, text=body.get("response", ""), data=body)
        except requests.RequestException as exc:
            return AIResult(success=False, error=str(exc))


def check_ollama_status() -> dict:
    provider = OllamaProvider()
    try:
        response = requests.get(f"{provider.host}/api/tags", timeout=5)
        if response.status_code != 200:
            return {"running": False, "models": []}
        body = response.json()
        models = [m.get("name", "") for m in body.get("models", [])]
        return {"running": True, "models": models}
    except requests.RequestException:
        return {"running": False, "models": []}

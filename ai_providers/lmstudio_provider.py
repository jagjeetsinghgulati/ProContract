from __future__ import annotations

import requests

from ai_providers.base_provider import AIResult, BaseAIProvider
from config import get_settings


class LMStudioProvider(BaseAIProvider):
    def __init__(self, model_name: str | None = None, host: str | None = None):
        settings = get_settings()
        self.host = host or settings.lmstudio_host
        super().__init__(model_name=model_name or settings.lmstudio_model)

    @property
    def provider_name(self) -> str:
        return "lmstudio"

    def initialize(self) -> bool:
        self._initialized = self.is_available()
        return self._initialized

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate(self, prompt: str, system_prompt: str | None = None) -> AIResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model_name, "messages": messages, "temperature": 0.1}
        try:
            response = requests.post(
                f"{self.host}/v1/chat/completions", json=payload, timeout=60
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            return AIResult(success=True, text=content, data=body)
        except (requests.RequestException, KeyError, IndexError) as exc:
            return AIResult(success=False, error=str(exc))


def check_lmstudio_status() -> dict:
    provider = LMStudioProvider()
    try:
        response = requests.get(f"{provider.host}/v1/models", timeout=5)
        if response.status_code != 200:
            return {"running": False, "models": []}
        body = response.json()
        models = [m.get("id", "") for m in body.get("data", [])]
        return {"running": True, "models": models}
    except requests.RequestException:
        return {"running": False, "models": []}

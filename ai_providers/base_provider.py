from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Any


class ProviderType(str, Enum):
    NONE = "none"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    GEMINI = "gemini"


@dataclass
class AIResult:
    success: bool
    data: dict[str, Any] | None = None
    text: str | None = None
    error: str | None = None
    latency_ms: float | None = None


class BaseAIProvider(ABC):
    def __init__(self, model_name: str):
        self._model_name = model_name
        self._initialized = False

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> AIResult:
        pass

    def extract_json(self, prompt: str, system_prompt: str | None = None) -> AIResult:
        started = perf_counter()
        raw = self.generate(prompt=prompt, system_prompt=system_prompt)
        if not raw.success or not raw.text:
            return raw
        parsed = parse_json_payload(raw.text)
        if parsed is None:
            return AIResult(
                success=False,
                text=raw.text,
                error="Provider response did not contain valid JSON.",
                latency_ms=(perf_counter() - started) * 1000,
            )
        return AIResult(
            success=True,
            data=parsed,
            text=raw.text,
            latency_ms=(perf_counter() - started) * 1000,
        )


def parse_json_payload(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    candidate = match.group(0)
    try:
        data = json.loads(candidate)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None

from __future__ import annotations

import time
from typing import Any

from openai import AsyncOpenAI

from ...config import get_settings
from ..types import LLMResult
from .openai_adapter import OpenAIAdapter, normalize_openai_usage


class GroqAdapter(OpenAIAdapter):
    provider_name = "groq"
    base_url = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.groq_api_key
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def normalize_usage(self, raw: Any):
        return normalize_openai_usage(raw)

    def get_model_catalog(self) -> list[dict[str, Any]]:
        from ...catalog import load_catalog

        return [item for item in load_catalog() if item["provider"] == "groq"]

    async def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        if not self.api_key:
            return LLMResult(
                provider=self.provider_name,
                model=model,
                status="failed",
                error_type="ProviderNotConfigured",
                raw_metadata={"message": "GROQ_API_KEY is not configured."},
            )
        started = time.perf_counter()
        result = await super().generate(model=model, messages=messages, tools=tools)
        if result.latency_ms == 0:
            result.latency_ms = int((time.perf_counter() - started) * 1000)
        return result

from __future__ import annotations

import time
from typing import Any

from ..catalog import get_model
from ..config import get_settings
from .adapters.groq_adapter import GroqAdapter
from .adapters.openai_adapter import OpenAIAdapter
from .pricing import estimate_cost
from .types import CostBreakdown, LLMResult, ProviderAdapter


class LLMGateway:
    def __init__(self, telemetry: Any | None = None) -> None:
        self.telemetry = telemetry
        settings = get_settings()
        self._adapters: dict[str, ProviderAdapter] = {
            "openai": OpenAIAdapter(api_key=settings.openai_api_key),
            "groq": GroqAdapter(api_key=settings.groq_api_key),
        }

    def get_adapter(self, provider: str) -> ProviderAdapter:
        adapter = self._adapters.get(provider)
        if adapter is None:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter

    async def generate(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        task_id: str,
        execution_id: str,
        sequence_no: int,
    ) -> tuple[LLMResult, CostBreakdown]:
        catalog_item = get_model(provider, model)
        if catalog_item is None or not catalog_item.get("enabled"):
            result = LLMResult(
                provider=provider,
                model=model,
                status="failed",
                error_type="InvalidModel",
                raw_metadata={"message": "This model is not currently configured."},
            )
            cost = estimate_cost(provider, model, result.usage)
            return result, cost

        adapter = self.get_adapter(provider)
        if self.telemetry:
            await self.telemetry.record_llm_start(
                execution_id=execution_id,
                sequence_no=sequence_no,
                provider=provider,
                model_id=model,
            )

        started = time.perf_counter()
        result = await adapter.generate(model=model, messages=messages, tools=tools)
        if result.latency_ms == 0:
            result.latency_ms = int((time.perf_counter() - started) * 1000)

        cost = estimate_cost(provider, model, result.usage)

        if self.telemetry:
            await self.telemetry.record_llm_complete(
                execution_id=execution_id,
                sequence_no=sequence_no,
                provider=provider,
                model_id=model,
                result=result,
                cost=cost,
                task_id=task_id,
            )

        return result, cost

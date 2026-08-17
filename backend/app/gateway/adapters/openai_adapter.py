from __future__ import annotations

import json
import time
from typing import Any

from openai import AsyncOpenAI

from ...config import get_settings
from ..types import LLMResult, NormalizedUsage, ToolCallRequest


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_openai_usage(raw: Any) -> NormalizedUsage:
    if raw is None:
        return NormalizedUsage(usage_available=False)

    if hasattr(raw, "model_dump"):
        data = raw.model_dump()
    elif isinstance(raw, dict):
        data = raw
    else:
        data = {
            "prompt_tokens": getattr(raw, "prompt_tokens", None),
            "completion_tokens": getattr(raw, "completion_tokens", None),
            "total_tokens": getattr(raw, "total_tokens", None),
            "prompt_tokens_details": getattr(raw, "prompt_tokens_details", None),
            "completion_tokens_details": getattr(raw, "completion_tokens_details", None),
        }

    prompt_details = data.get("prompt_tokens_details") or {}
    completion_details = data.get("completion_tokens_details") or {}
    if hasattr(prompt_details, "model_dump"):
        prompt_details = prompt_details.model_dump()
    if hasattr(completion_details, "model_dump"):
        completion_details = completion_details.model_dump()

    input_tokens = _optional_int(data.get("prompt_tokens") or data.get("input_tokens"))
    output_tokens = _optional_int(data.get("completion_tokens") or data.get("output_tokens"))
    total_tokens = _optional_int(data.get("total_tokens"))
    cached_tokens = _optional_int(
        (prompt_details or {}).get("cached_tokens") or data.get("cached_tokens")
    )
    reasoning_tokens = _optional_int(
        (completion_details or {}).get("reasoning_tokens") or data.get("reasoning_tokens")
    )
    tool_tokens = _optional_int(data.get("tool_tokens"))

    usage_available = any(
        value is not None
        for value in (input_tokens, output_tokens, total_tokens, cached_tokens, reasoning_tokens)
    )
    return NormalizedUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cached_tokens=cached_tokens,
        reasoning_tokens=reasoning_tokens,
        tool_tokens=tool_tokens,
        usage_available=usage_available,
    )


def _parse_arguments(raw: str | dict | None) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"_raw": parsed}
    except json.JSONDecodeError:
        return {"_raw": raw}


class OpenAIAdapter:
    provider_name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    def normalize_usage(self, raw: Any) -> NormalizedUsage:
        return normalize_openai_usage(raw)

    def get_model_catalog(self) -> list[dict[str, Any]]:
        from ...catalog import load_catalog

        return [item for item in load_catalog() if item["provider"] == "openai"]

    async def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        started = time.perf_counter()
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return LLMResult(
                text=None,
                provider=self.provider_name,
                model=model,
                latency_ms=latency_ms,
                status="failed",
                error_type=exc.__class__.__name__,
                raw_metadata={"error": str(exc)},
            )

        latency_ms = int((time.perf_counter() - started) * 1000)
        choice = response.choices[0] if response.choices else None
        message = choice.message if choice else None
        tool_calls: list[ToolCallRequest] = []
        if message and message.tool_calls:
            for call in message.tool_calls:
                fn = call.function
                tool_calls.append(
                    ToolCallRequest(
                        id=call.id,
                        name=fn.name,
                        arguments=_parse_arguments(fn.arguments),
                    )
                )

        usage = self.normalize_usage(getattr(response, "usage", None))
        return LLMResult(
            text=message.content if message else None,
            tool_calls=tool_calls,
            usage=usage,
            provider=self.provider_name,
            model=model,
            latency_ms=latency_ms,
            status="completed",
            model_version=getattr(response, "system_fingerprint", None),
            raw_metadata={
                "finish_reason": getattr(choice, "finish_reason", None),
                "id": getattr(response, "id", None),
            },
        )

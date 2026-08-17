from typing import Any, Protocol

from pydantic import BaseModel, Field


class NormalizedUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    tool_tokens: int | None = None
    usage_available: bool = False


class ToolCallRequest(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResult(BaseModel):
    text: str | None = None
    tool_calls: list[ToolCallRequest] = Field(default_factory=list)
    usage: NormalizedUsage = Field(default_factory=NormalizedUsage)
    provider: str
    model: str
    latency_ms: int = 0
    queue_time_ms: int | None = None
    status: str = "completed"
    error_type: str | None = None
    model_version: str | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class CostBreakdown(BaseModel):
    pricing_version: str | None = None
    input_usd_per_1m: float | None = None
    output_usd_per_1m: float | None = None
    cache_read_usd_per_1m: float | None = None
    input_cost_usd: float | None = None
    output_cost_usd: float | None = None
    estimated_cost_usd: float | None = None
    pricing_available: bool = False


class ProviderAdapter(Protocol):
    provider_name: str

    async def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult: ...

    def normalize_usage(self, raw: Any) -> NormalizedUsage: ...

    def get_model_catalog(self) -> list[dict[str, Any]]: ...

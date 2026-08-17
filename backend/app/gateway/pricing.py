import json
from functools import lru_cache
from pathlib import Path

from .types import CostBreakdown, NormalizedUsage

PRICING_PATH = Path(__file__).resolve().parent.parent / "data" / "pricing.json"


@lru_cache
def load_pricing() -> list[dict]:
    return json.loads(PRICING_PATH.read_text(encoding="utf-8"))


def get_pricing(provider: str, model: str) -> dict | None:
    for row in load_pricing():
        if row["provider"] == provider and row["model"] == model:
            return row
    return None


def _cost(tokens: int | None, usd_per_1m: float | None) -> float | None:
    if tokens is None or usd_per_1m is None:
        return None
    return tokens / 1_000_000 * usd_per_1m


def estimate_cost(provider: str, model: str, usage: NormalizedUsage) -> CostBreakdown:
    row = get_pricing(provider, model)
    if row is None:
        return CostBreakdown(pricing_available=False)

    billed_input = usage.input_tokens
    cached = usage.cached_tokens
    cache_price = row.get("cache_read_usd_per_1m")
    input_price = row.get("input_usd_per_1m")
    output_price = row.get("output_usd_per_1m")

    input_cost = None
    if billed_input is not None and input_price is not None:
        uncached = billed_input
        cached_cost = None
        if cached is not None:
            uncached = max(billed_input - cached, 0)
            cached_cost = _cost(cached, cache_price if cache_price is not None else input_price)
        uncached_cost = _cost(uncached, input_price)
        parts = [value for value in (uncached_cost, cached_cost) if value is not None]
        input_cost = sum(parts) if parts else None

    output_cost = _cost(usage.output_tokens, output_price)
    estimated = None
    if input_cost is not None or output_cost is not None:
        estimated = (input_cost or 0) + (output_cost or 0)

    return CostBreakdown(
        pricing_version=row.get("pricing_version"),
        input_usd_per_1m=input_price,
        output_usd_per_1m=output_price,
        cache_read_usd_per_1m=cache_price,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        estimated_cost_usd=estimated,
        pricing_available=True,
    )

import json
from pathlib import Path

from app.gateway.adapters.openai_adapter import normalize_openai_usage
from app.gateway.pricing import estimate_cost, get_pricing
from app.gateway.types import NormalizedUsage

CATALOG_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "model_catalog.json"


def test_usage_maps_openai_fields():
    usage = normalize_openai_usage(
        {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
            "prompt_tokens_details": {"cached_tokens": 200},
            "completion_tokens_details": {"reasoning_tokens": 12},
        }
    )
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.cached_tokens == 200
    assert usage.reasoning_tokens == 12
    assert usage.usage_available is True


def test_missing_usage_is_none_not_zero():
    usage = normalize_openai_usage(None)
    assert usage.input_tokens is None
    assert usage.output_tokens is None
    assert usage.total_tokens is None
    assert usage.cached_tokens is None
    assert usage.usage_available is False


def test_partial_usage_does_not_fill_zeros():
    usage = normalize_openai_usage({"prompt_tokens": 10})
    assert usage.input_tokens == 10
    assert usage.output_tokens is None
    assert usage.total_tokens is None


def test_cost_from_configured_pricing():
    usage = NormalizedUsage(input_tokens=1_000_000, output_tokens=1_000_000, usage_available=True)
    cost = estimate_cost("openai", "gpt-4o-mini", usage)
    assert cost.pricing_available is True
    assert cost.input_cost_usd == 0.15
    assert cost.output_cost_usd == 0.60
    assert abs((cost.estimated_cost_usd or 0) - 0.75) < 1e-9


def test_every_enabled_model_has_pricing():
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    unpriced = [
        f"{item['provider']}/{item['model_id']}"
        for item in catalog
        if item.get("enabled") and get_pricing(item["provider"], item["model_id"]) is None
    ]
    assert not unpriced, f"enabled models without pricing show cost as N/A: {unpriced}"


def test_unknown_model_cost_is_unavailable():
    usage = NormalizedUsage(input_tokens=100, output_tokens=50, usage_available=True)
    cost = estimate_cost("openai", "unknown-model", usage)
    assert cost.pricing_available is False
    assert cost.estimated_cost_usd is None

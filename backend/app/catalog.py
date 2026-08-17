import json
from functools import lru_cache
from pathlib import Path

from .config import get_settings

CATALOG_PATH = Path(__file__).parent / "data" / "model_catalog.json"
PROVIDER_LABELS = {"openai": "OpenAI", "groq": "Groq"}


@lru_cache
def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def public_models() -> list[dict]:
    settings = get_settings()
    models = []
    for item in load_catalog():
        if not item.get("enabled"):
            continue
        provider = item["provider"]
        configured = (
            settings.openai_configured
            if provider == "openai"
            else settings.groq_configured
            if provider == "groq"
            else False
        )
        models.append(
            {
                "provider": item["provider"],
                "model_id": item["model_id"],
                "display_name": item["display_name"],
                "context_window": item.get("context_window"),
                "supports_tools": item.get("supports_tools", True),
                "supports_rag": item.get("supports_rag", True),
                "configured": configured,
            }
        )
    return models


def get_model(provider: str, model_id: str) -> dict | None:
    for item in load_catalog():
        if item["provider"] == provider and item["model_id"] == model_id:
            return item
    return None


def provider_label(provider: str) -> str:
    return PROVIDER_LABELS.get(provider, provider)


def model_display_name(provider: str, model_id: str) -> str:
    item = get_model(provider, model_id)
    if item and item.get("display_name"):
        return str(item["display_name"])
    if model_id and "/" in model_id:
        return model_id.rsplit("/", 1)[-1]
    return model_id or "Unknown"


def model_label(provider: str, model_id: str) -> str:
    return f"{provider_label(provider)} / {model_display_name(provider, model_id)}"

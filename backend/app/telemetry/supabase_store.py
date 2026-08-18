from __future__ import annotations

import logging
from typing import Any

from ..config import get_settings

logger = logging.getLogger(__name__)

_client = None
_client_failed = False


def get_supabase():
    global _client, _client_failed
    settings = get_settings()
    if not settings.supabase_configured or _client_failed:
        return None
    if _client is None:
        try:
            from supabase import create_client

            _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        except Exception as exc:
            logger.warning("Supabase client unavailable: %s", exc)
            _client_failed = True
            return None
    return _client


def persist(table: str, row: dict[str, Any], *, upsert: bool = False) -> None:
    client = get_supabase()
    if client is None:
        return
    try:
        query = client.table(table)
        if upsert:
            query.upsert(row).execute()
        else:
            query.insert(row).execute()
    except Exception as exc:
        logger.warning("Telemetry persist failed for %s: %s", table, exc)


def persist_update(table: str, key: str, value: str, patch: dict[str, Any]) -> None:
    client = get_supabase()
    if client is None:
        return
    try:
        client.table(table).update(patch).eq(key, value).execute()
    except Exception as exc:
        logger.warning("Telemetry update failed for %s: %s", table, exc)

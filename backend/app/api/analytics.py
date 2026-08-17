from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from ..telemetry.analytics import comparison, history, model_analytics, overview, tool_analytics
from ..telemetry.recorder import recorder

router = APIRouter()


class ComparisonGroupRequest(BaseModel):
    name: str
    description: str | None = None


def _installation(x_installation_id: str | None) -> str:
    if not x_installation_id:
        raise HTTPException(status_code=400, detail="X-Installation-Id header is required")
    return x_installation_id


def _filters(
    start: str | None,
    end: str | None,
    provider: str | None,
    model: str | None,
    task_type: str | None,
    comparison_group_id: str | None,
    outcome: str | None,
    rag_enabled: bool | None,
    has_tool_calls: bool | None,
    has_retries: bool | None,
) -> dict[str, Any]:
    return {
        "start": start,
        "end": end,
        "provider": provider,
        "model": model,
        "task_type": task_type,
        "comparison_group_id": comparison_group_id,
        "outcome": outcome,
        "rag_enabled": rag_enabled,
        "has_tool_calls": has_tool_calls,
        "has_retries": has_retries,
    }


@router.get("/api/analytics/overview")
async def analytics_overview(
    start: str | None = None,
    end: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    task_type: str | None = None,
    comparison_group_id: str | None = None,
    outcome: str | None = None,
    rag_enabled: bool | None = Query(default=None),
    has_tool_calls: bool | None = Query(default=None),
    has_retries: bool | None = Query(default=None),
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    filters = _filters(start, end, provider, model, task_type, comparison_group_id, outcome, rag_enabled, has_tool_calls, has_retries)
    return overview(installation_id, filters)


@router.get("/api/analytics/models")
async def analytics_models(
    start: str | None = None,
    end: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    task_type: str | None = None,
    comparison_group_id: str | None = None,
    outcome: str | None = None,
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    filters = _filters(start, end, provider, model, task_type, comparison_group_id, outcome, None, None, None)
    return {"models": model_analytics(installation_id, filters)}


@router.get("/api/analytics/tools")
async def analytics_tools(
    start: str | None = None,
    end: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    task_type: str | None = None,
    comparison_group_id: str | None = None,
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    filters = _filters(start, end, provider, model, task_type, comparison_group_id, None, None, None, None)
    return {"tools": tool_analytics(installation_id, filters)}


@router.get("/api/analytics/history")
async def analytics_history(
    start: str | None = None,
    end: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    task_type: str | None = None,
    comparison_group_id: str | None = None,
    outcome: str | None = None,
    rag_enabled: bool | None = Query(default=None),
    has_tool_calls: bool | None = Query(default=None),
    has_retries: bool | None = Query(default=None),
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    filters = _filters(start, end, provider, model, task_type, comparison_group_id, outcome, rag_enabled, has_tool_calls, has_retries)
    return {"executions": history(installation_id, filters)}


@router.get("/api/analytics/comparisons/{comparison_group_id}")
async def analytics_comparison(
    comparison_group_id: str,
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    return comparison(installation_id, comparison_group_id)


@router.post("/api/comparison-groups")
async def create_group(
    payload: ComparisonGroupRequest,
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    return await recorder.create_comparison_group(installation_id, payload.name, payload.description)


@router.get("/api/comparison-groups")
async def list_groups(x_installation_id: str | None = Header(default=None)) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    return {"groups": recorder.store.list_comparison_groups(installation_id)}

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..agent.control import clear_run, register_run, request_stop
from ..agent.runtime import run_agent
from ..catalog import get_model
from ..config import get_settings
from ..telemetry.analytics import execution_detail, fingerprint
from ..telemetry.memory import memory_store
from ..telemetry.recorder import recorder

router = APIRouter()


class ModelRef(BaseModel):
    provider: str
    model_id: str


class ExecutionRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20_000)
    model: ModelRef
    task_type: str = "general"
    comparison_group_id: str | None = None
    workspace_id: str = "demo-workspace"
    rag_enabled: bool = False


def _installation(x_installation_id: str | None) -> str:
    if not x_installation_id:
        raise HTTPException(status_code=400, detail="X-Installation-Id header is required")
    return x_installation_id


@router.post("/api/executions")
async def start_execution(
    payload: ExecutionRequest,
    x_installation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    catalog_item = get_model(payload.model.provider, payload.model.model_id)
    if catalog_item is None or not catalog_item.get("enabled"):
        raise HTTPException(status_code=400, detail="This model is not currently configured.")
    settings = get_settings()
    if payload.model.provider == "openai" and not settings.openai_configured:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured.")
    if payload.model.provider == "groq" and not settings.groq_configured:
        raise HTTPException(status_code=400, detail="GROQ_API_KEY is not configured.")

    execution = await recorder.start_execution(
        installation_id=installation_id,
        workspace_id=payload.workspace_id,
        task_text=payload.task,
        task_type=payload.task_type or "general",
        rag_enabled=payload.rag_enabled,
        comparison_group_id=payload.comparison_group_id,
        provider=payload.model.provider,
        model_id=payload.model.model_id,
    )
    task = asyncio.create_task(
        run_agent(
            execution_id=execution["id"],
            task=payload.task,
            provider=payload.model.provider,
            model_id=payload.model.model_id,
            rag_enabled=payload.rag_enabled,
            task_type=payload.task_type,
        )
    )
    register_run(execution["id"], task)
    task.add_done_callback(lambda _task, execution_id=execution["id"]: clear_run(execution_id))
    return {"execution_id": execution["id"], "status": "started"}


@router.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str, x_installation_id: str | None = Header(default=None)) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    detail = execution_detail(execution_id)
    if not detail or detail["execution"].get("installation_id") != installation_id:
        raise HTTPException(status_code=404, detail="Execution not found")
    return detail


@router.get("/api/executions/{execution_id}/events")
async def get_events(execution_id: str, x_installation_id: str | None = Header(default=None)) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    execution = memory_store.get_execution(execution_id)
    if not execution or execution.get("installation_id") != installation_id:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "execution_id": execution_id,
        "status": execution.get("status"),
        "fingerprint": fingerprint(execution),
        "events": memory_store.events_for(execution_id),
        "final_output": execution.get("final_output"),
        "outcome": execution.get("outcome"),
    }


@router.post("/api/executions/{execution_id}/stop")
async def stop_execution(execution_id: str, x_installation_id: str | None = Header(default=None)) -> dict[str, Any]:
    installation_id = _installation(x_installation_id)
    execution = memory_store.get_execution(execution_id)
    if not execution or execution.get("installation_id") != installation_id:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.get("status") not in {"running", "queued"}:
        return {"execution_id": execution_id, "status": execution.get("status")}
    request_stop(execution_id)
    stopped = await recorder.stop_execution(execution_id, "Stopped by user.")
    return {"execution_id": execution_id, "status": (stopped or execution).get("status")}

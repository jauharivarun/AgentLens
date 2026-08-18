from __future__ import annotations

import hashlib
import logging
from typing import Any

from ..catalog import model_label
from ..gateway.types import CostBreakdown, LLMResult
from .memory import elapsed_ms, iso, memory_store, new_id, utcnow
from . import supabase_store

logger = logging.getLogger(__name__)


SUMMARY_FIELDS = (
    "model_version",
    "llm_call_count",
    "tool_call_count",
    "retry_count",
    "files_read_count",
    "files_modified_count",
    "command_count",
    "rag_query_count",
    "chunks_retrieved",
    "tests_run",
    "tests_passed",
    "estimated_cost_usd",
    "time_to_first_edit_ms",
    "tool_error_count",
    "files_touched_count",
    "lines_added",
    "lines_removed",
    "edit_count",
    "correction_detected",
    "abandoned",
)


def _summary_patch(execution: dict[str, Any]) -> dict[str, Any]:
    """Live counters accumulated in memory, ready to persist alongside a status change."""
    return {field: execution.get(field) for field in SUMMARY_FIELDS}


class TelemetryRecorder:
    def __init__(self) -> None:
        self.store = memory_store

    async def touch_installation(self, installation_id: str) -> None:
        self.store.upsert_installation(installation_id)
        supabase_store.persist("installations", self.store.installations[installation_id], upsert=True)

    async def start_execution(
        self,
        *,
        installation_id: str,
        workspace_id: str,
        task_text: str,
        task_type: str,
        rag_enabled: bool,
        comparison_group_id: str | None,
        provider: str,
        model_id: str,
    ) -> dict[str, Any]:
        await self.touch_installation(installation_id)
        workspace = self.store.ensure_workspace(installation_id, workspace_id)
        supabase_store.persist("workspaces", workspace, upsert=True)

        task_id = new_id()
        execution_id = new_id()
        now = iso(utcnow())
        task = {
            "id": task_id,
            "installation_id": installation_id,
            "workspace_id": workspace_id,
            "task_text": task_text,
            "task_type": task_type,
            "rag_enabled": rag_enabled,
            "comparison_group_id": comparison_group_id,
            "created_at": now,
        }
        self.store.insert_task(task)
        supabase_store.persist("tasks", task)

        execution = {
            "id": execution_id,
            "task_id": task_id,
            "installation_id": installation_id,
            "workspace_id": workspace_id,
            "comparison_group_id": comparison_group_id,
            "provider": provider,
            "model_id": model_id,
            "model_version": None,
            "status": "running",
            "started_at": now,
            "completed_at": None,
            "duration_ms": None,
            "llm_call_count": 0,
            "tool_call_count": 0,
            "retry_count": 0,
            "files_read_count": 0,
            "files_modified_count": 0,
            "command_count": 0,
            "rag_query_count": 0,
            "chunks_retrieved": 0,
            "tests_run": 0,
            "tests_passed": 0,
            "outcome": None,
            "final_output": None,
            "estimated_cost_usd": None,
            "time_to_first_edit_ms": None,
            "tool_error_count": 0,
            "files_touched_count": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "edit_count": 0,
            "correction_detected": False,
            "abandoned": False,
            "task_text": task_text,
            "task_type": task_type,
            "rag_enabled": rag_enabled,
            "pricing_known": False,
            "sequence_counter": 0,
            "files_touched": [],
            "metadata": {},
        }
        self.store.insert_execution(execution)
        persistable = {k: v for k, v in execution.items() if k not in {"sequence_counter", "files_touched", "task_text", "task_type", "rag_enabled", "pricing_known"}}
        supabase_store.persist("executions", persistable)

        await self.record_execution_event(
            execution_id,
            "execution_started",
            "Execution started",
            {"provider": provider, "model_id": model_id},
        )
        await self.record_execution_event(
            execution_id,
            "user_message",
            "User task received",
            {"task_type": task_type, "rag_enabled": rag_enabled},
        )
        return execution

    def _next_seq(self, execution_id: str) -> int:
        execution = self.store.get_execution(execution_id)
        if not execution:
            return 1
        execution["sequence_counter"] = int(execution.get("sequence_counter") or 0) + 1
        return execution["sequence_counter"]

    async def record_execution_event(
        self,
        execution_id: str,
        event_type: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
        sequence_no: int | None = None,
    ) -> dict[str, Any]:
        seq = sequence_no or self._next_seq(execution_id)
        row = {
            "id": new_id(),
            "execution_id": execution_id,
            "sequence_no": seq,
            "event_type": event_type,
            "event_time": iso(utcnow()),
            "summary": summary,
            "metadata": metadata or {},
        }
        self.store.append_event(row)
        supabase_store.persist("execution_events", row)
        return row

    async def record_llm_start(
        self,
        *,
        execution_id: str,
        sequence_no: int,
        provider: str,
        model_id: str,
    ) -> None:
        await self.record_execution_event(
            execution_id,
            "llm_started",
            f"LLM call started ({model_label(provider, model_id)})",
            {"provider": provider, "model_id": model_id, "call_number": sequence_no},
        )

    async def record_llm_complete(
        self,
        *,
        execution_id: str,
        sequence_no: int,
        provider: str,
        model_id: str,
        result: LLMResult,
        cost: CostBreakdown,
        task_id: str,
    ) -> None:
        execution = self.store.get_execution(execution_id)
        now = iso(utcnow())
        row = {
            "id": new_id(),
            "execution_id": execution_id,
            "sequence_no": sequence_no,
            "provider": provider,
            "model_id": model_id,
            "model_version": result.model_version,
            "started_at": now,
            "completed_at": now,
            "latency_ms": result.latency_ms,
            "queue_time_ms": result.queue_time_ms,
            "input_tokens": result.usage.input_tokens,
            "output_tokens": result.usage.output_tokens,
            "total_tokens": result.usage.total_tokens,
            "cached_tokens": result.usage.cached_tokens,
            "reasoning_tokens": result.usage.reasoning_tokens,
            "tool_tokens": result.usage.tool_tokens,
            "usage_available": result.usage.usage_available,
            "input_cost_usd": cost.input_cost_usd,
            "output_cost_usd": cost.output_cost_usd,
            "estimated_cost_usd": cost.estimated_cost_usd,
            "pricing_version": cost.pricing_version,
            "status": result.status,
            "error_type": result.error_type,
            "metadata": {
                "task_id": task_id,
                "pricing_available": cost.pricing_available,
                "source": "provider_reported" if result.usage.usage_available else "unavailable",
            },
        }
        self.store.append_llm(row)
        supabase_store.persist("llm_events", row)

        if execution:
            execution["llm_call_count"] = int(execution.get("llm_call_count") or 0) + 1
            if result.model_version:
                execution["model_version"] = result.model_version
            if cost.estimated_cost_usd is not None:
                current = execution.get("estimated_cost_usd") or 0
                execution["estimated_cost_usd"] = float(current) + float(cost.estimated_cost_usd)
                execution["pricing_known"] = True
            if result.status == "failed":
                execution["retry_count"] = int(execution.get("retry_count") or 0) + 1

        usage_bits = []
        if result.usage.input_tokens is not None:
            usage_bits.append(f"{result.usage.input_tokens:,} input")
        if result.usage.output_tokens is not None:
            usage_bits.append(f"{result.usage.output_tokens:,} output")
        usage_text = " / ".join(usage_bits) if usage_bits else "usage not reported"
        await self.record_execution_event(
            execution_id,
            "llm_completed" if result.status != "failed" else "retry",
            f"LLM call completed — {usage_text}",
            {
                "provider": provider,
                "model_id": model_id,
                "latency_ms": result.latency_ms,
                "usage": result.usage.model_dump(),
                "estimated_cost_usd": cost.estimated_cost_usd,
                "status": result.status,
                "error_type": result.error_type,
            },
        )

    async def record_tool_start(
        self,
        *,
        execution_id: str,
        tool_name: str,
        input_metadata: dict[str, Any],
        retry_no: int = 0,
    ) -> dict[str, Any]:
        seq = self._next_seq(execution_id)
        row = {
            "id": new_id(),
            "execution_id": execution_id,
            "sequence_no": seq,
            "tool_name": tool_name,
            "started_at": iso(utcnow()),
            "completed_at": None,
            "latency_ms": None,
            "status": "running",
            "retry_no": retry_no,
            "input_metadata": input_metadata,
            "output_metadata": None,
            "error_type": None,
        }
        self.store.append_tool(row)
        await self.record_execution_event(
            execution_id,
            "tool_started",
            f"Tool: {tool_name}",
            {"tool_name": tool_name, "input": input_metadata, "retry_no": retry_no},
            sequence_no=None,
        )
        if tool_name == "rag_search":
            await self.record_execution_event(execution_id, "rag_started", "RAG retrieval started", input_metadata)
        return row

    async def record_tool_complete(
        self,
        *,
        tool_event_id: str,
        execution_id: str,
        tool_name: str,
        status: str,
        latency_ms: int,
        output_metadata: dict[str, Any] | None = None,
        error_type: str | None = None,
        retry_no: int = 0,
    ) -> None:
        tool_row = next((row for row in self.store.tool_events if row["id"] == tool_event_id), None)
        if tool_row:
            tool_row["completed_at"] = iso(utcnow())
            tool_row["latency_ms"] = latency_ms
            tool_row["status"] = status
            tool_row["output_metadata"] = output_metadata
            tool_row["error_type"] = error_type
            supabase_store.persist("tool_events", tool_row)

        execution = self.store.get_execution(execution_id)
        if execution:
            execution["tool_call_count"] = int(execution.get("tool_call_count") or 0) + 1
            if status != "success":
                execution["tool_error_count"] = int(execution.get("tool_error_count") or 0) + 1
            if retry_no:
                execution["retry_count"] = int(execution.get("retry_count") or 0) + retry_no
            if tool_name == "read_file":
                execution["files_read_count"] = int(execution.get("files_read_count") or 0) + 1
            if tool_name == "run_command":
                execution["command_count"] = int(execution.get("command_count") or 0) + 1
            if tool_name == "rag_search":
                execution["rag_query_count"] = int(execution.get("rag_query_count") or 0) + 1
                execution["chunks_retrieved"] = int(execution.get("chunks_retrieved") or 0) + int(
                    (output_metadata or {}).get("result_count") or 0
                )

        event_type = "tool_completed"
        if status != "success":
            event_type = "retry" if retry_no else "tool_completed"
        await self.record_execution_event(
            execution_id,
            event_type,
            f"Tool {tool_name} {status}",
            {
                "tool_name": tool_name,
                "status": status,
                "latency_ms": latency_ms,
                "error_type": error_type,
                "output": output_metadata,
            },
        )
        if tool_name == "rag_search":
            await self.record_execution_event(
                execution_id,
                "rag_completed",
                "RAG retrieval completed",
                output_metadata or {},
            )

    async def record_rag_event(self, *, execution_id: str, payload: dict[str, Any]) -> None:
        row = {
            "id": new_id(),
            "execution_id": execution_id,
            "sequence_no": self._next_seq(execution_id),
            "query_hash": payload.get("query_hash"),
            "top_k": payload.get("top_k", 0),
            "result_count": payload.get("result_count", 0),
            "retrieval_latency_ms": payload.get("retrieval_latency_ms"),
            "retrieved_chunk_count": payload.get("retrieved_chunk_count"),
            "estimated_retrieved_tokens": payload.get("estimated_retrieved_tokens"),
            "context_selected_tokens": payload.get("context_selected_tokens"),
            "metadata": payload.get("metadata") or {},
            "created_at": iso(utcnow()),
        }
        self.store.append_rag(row)
        supabase_store.persist("rag_events", row)

    async def record_edit_event(
        self,
        *,
        execution_id: str,
        file_path: str,
        operation: str,
        lines_added: int,
        lines_removed: int,
        content_size_before: int | None,
        content_size_after: int | None,
        is_repeat: bool,
    ) -> None:
        execution = self.store.get_execution(execution_id)
        started = None
        if execution:
            started = execution.get("started_at")
            touched = list(execution.get("files_touched") or [])
            if file_path not in touched:
                touched.append(file_path)
            execution["files_touched"] = touched
            execution["files_touched_count"] = len(touched)
            if operation in {"write", "update"}:
                execution["files_modified_count"] = int(execution.get("files_modified_count") or 0) + (0 if is_repeat else 1)
                execution["edit_count"] = int(execution.get("edit_count") or 0) + 1
                execution["lines_added"] = int(execution.get("lines_added") or 0) + lines_added
                execution["lines_removed"] = int(execution.get("lines_removed") or 0) + lines_removed
                if execution.get("time_to_first_edit_ms") is None and started:
                    from datetime import datetime

                    try:
                        start_dt = datetime.fromisoformat(started)
                        execution["time_to_first_edit_ms"] = int((utcnow() - start_dt).total_seconds() * 1000)
                    except ValueError:
                        pass

        row = {
            "id": new_id(),
            "execution_id": execution_id,
            "sequence_no": self._next_seq(execution_id),
            "file_path": file_path,
            "operation": operation,
            "timestamp": iso(utcnow()),
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "changed_lines": lines_added + lines_removed,
            "content_size_before": content_size_before,
            "content_size_after": content_size_after,
            "is_repeat_file_edit": is_repeat,
        }
        self.store.append_edit(row)
        supabase_store.persist("edit_events", row)
        await self.record_execution_event(
            execution_id,
            "file_edit",
            f"Edited {file_path} (+{lines_added}/-{lines_removed})",
            {"file_path": file_path, "lines_added": lines_added, "lines_removed": lines_removed},
        )

    async def complete_execution(self, execution_id: str, final_output: str, outcome: str = "success") -> dict[str, Any] | None:
        execution = self.store.get_execution(execution_id)
        if not execution:
            return None
        if execution.get("status") not in {"running", "queued"}:
            return execution
        completed = utcnow()
        duration = elapsed_ms(execution.get("started_at"), completed)
        patch = {
            "status": "completed",
            "completed_at": iso(completed),
            "duration_ms": duration,
            "outcome": outcome,
            "final_output": final_output,
        }
        self.store.update_execution(execution_id, patch)
        supabase_store.persist_update("executions", "id", execution_id, {**patch, **_summary_patch(execution)})
        await self.record_execution_event(execution_id, "execution_completed", "Execution completed", {"outcome": outcome})
        return self.store.get_execution(execution_id)

    async def fail_execution(self, execution_id: str, error: str, outcome: str = "failed") -> dict[str, Any] | None:
        execution = self.store.get_execution(execution_id)
        if not execution:
            return None
        if execution.get("status") not in {"running", "queued"}:
            return execution
        completed = utcnow()
        duration = elapsed_ms(execution.get("started_at"), completed)
        patch = {
            "status": "failed",
            "completed_at": iso(completed),
            "duration_ms": duration,
            "outcome": outcome,
            "final_output": error,
        }
        self.store.update_execution(execution_id, patch)
        supabase_store.persist_update("executions", "id", execution_id, {**patch, **_summary_patch(execution)})
        await self.record_execution_event(
            execution_id,
            "execution_failed",
            "Execution failed",
            {"error": error},
        )
        return self.store.get_execution(execution_id)

    async def stop_execution(self, execution_id: str, message: str = "Stopped by user.") -> dict[str, Any] | None:
        execution = self.store.get_execution(execution_id)
        if not execution:
            return None
        if execution.get("status") not in {"running", "queued"}:
            return execution
        completed = utcnow()
        duration = elapsed_ms(execution.get("started_at"), completed)
        patch = {
            "status": "cancelled",
            "completed_at": iso(completed),
            "duration_ms": duration,
            "outcome": "cancelled",
            "final_output": message,
        }
        self.store.update_execution(execution_id, patch)
        supabase_store.persist_update("executions", "id", execution_id, {**patch, **_summary_patch(execution)})
        await self.record_execution_event(
            execution_id,
            "execution_cancelled",
            "Execution stopped",
            {"reason": message},
        )
        return self.store.get_execution(execution_id)

    async def create_comparison_group(self, installation_id: str, name: str, description: str | None) -> dict[str, Any]:
        await self.touch_installation(installation_id)
        row = {
            "id": new_id(),
            "installation_id": installation_id,
            "name": name,
            "description": description,
            "created_at": iso(utcnow()),
        }
        self.store.insert_comparison_group(row)
        supabase_store.persist("comparison_groups", row)
        return row


recorder = TelemetryRecorder()


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

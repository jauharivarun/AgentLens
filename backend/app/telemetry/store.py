"""Read facade over telemetry.

Writes always land in :mod:`memory` (live, in-process) and are mirrored to Supabase by the
recorder. Reads come from both: Supabase supplies history that outlived the process, memory
supplies whatever is happening right now. Memory wins on conflict because a running execution
only has its live counters there.

When Supabase is not configured every call degrades to memory alone, which is the original
behaviour.
"""

from __future__ import annotations

from typing import Any

from . import supabase_store
from .memory import memory_store


def _merge(remote: list[dict[str, Any]] | None, local: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not remote:
        return local
    by_id: dict[str, dict[str, Any]] = {row["id"]: row for row in remote if row.get("id")}
    for row in local:
        by_id[row["id"]] = row
    return list(by_id.values())


def _by_execution(table: str, execution_id: str, local: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remote = supabase_store.fetch(table, eq={"execution_id": execution_id})
    return _merge(remote, local)


def list_executions(installation_id: str) -> list[dict[str, Any]]:
    remote = supabase_store.fetch("executions", eq={"installation_id": installation_id})
    rows = _merge(remote, memory_store.list_executions(installation_id))
    rows.sort(key=lambda item: item.get("started_at") or "", reverse=True)
    return rows


def get_execution(execution_id: str) -> dict[str, Any] | None:
    live = memory_store.get_execution(execution_id)
    if live:
        return live
    remote = supabase_store.fetch("executions", eq={"id": execution_id})
    return remote[0] if remote else None


def get_task(task_id: str | None) -> dict[str, Any]:
    if not task_id:
        return {}
    local = memory_store.tasks.get(task_id)
    if local:
        return local
    remote = supabase_store.fetch("tasks", eq={"id": task_id})
    return remote[0] if remote else {}


def events_for(execution_id: str) -> list[dict[str, Any]]:
    rows = _by_execution("execution_events", execution_id, memory_store.events_for(execution_id))
    rows.sort(key=lambda item: item.get("sequence_no") or 0)
    return rows


def llm_for(execution_id: str) -> list[dict[str, Any]]:
    return _by_execution("llm_events", execution_id, memory_store.llm_for(execution_id))


def tools_for(execution_id: str) -> list[dict[str, Any]]:
    return _by_execution("tool_events", execution_id, memory_store.tools_for(execution_id))


def rag_for(execution_id: str) -> list[dict[str, Any]]:
    return _by_execution("rag_events", execution_id, memory_store.rag_for(execution_id))


def edits_for(execution_id: str) -> list[dict[str, Any]]:
    return _by_execution("edit_events", execution_id, memory_store.edits_for(execution_id))


def list_comparison_groups(installation_id: str) -> list[dict[str, Any]]:
    remote = supabase_store.fetch("comparison_groups", eq={"installation_id": installation_id})
    rows = _merge(remote, memory_store.list_comparison_groups(installation_id))
    rows.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return rows


def get_comparison_group(comparison_group_id: str) -> dict[str, Any] | None:
    local = memory_store.comparison_groups.get(comparison_group_id)
    if local:
        return local
    remote = supabase_store.fetch("comparison_groups", eq={"id": comparison_group_id})
    return remote[0] if remote else None


def _group_by_execution(
    table: str, execution_ids: list[str], local_for: Any
) -> dict[str, list[dict[str, Any]]]:
    """One round trip for many executions instead of one per execution."""
    grouped: dict[str, list[dict[str, Any]]] = {execution_id: [] for execution_id in execution_ids}
    remote = supabase_store.fetch(table, in_={"execution_id": execution_ids})
    for row in remote or []:
        grouped.setdefault(row.get("execution_id"), []).append(row)
    for execution_id in execution_ids:
        grouped[execution_id] = _merge(grouped.get(execution_id), local_for(execution_id))
    return grouped


def llm_for_many(execution_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    return _group_by_execution("llm_events", execution_ids, memory_store.llm_for)


def tools_for_many(execution_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    return _group_by_execution("tool_events", execution_ids, memory_store.tools_for)


def get_tasks_many(task_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Task rows for many executions in one round trip."""
    wanted = [task_id for task_id in dict.fromkeys(task_ids) if task_id]
    if not wanted:
        return {}
    tasks = {task_id: memory_store.tasks[task_id] for task_id in wanted if task_id in memory_store.tasks}
    missing = [task_id for task_id in wanted if task_id not in tasks]
    if missing:
        for row in supabase_store.fetch("tasks", in_={"id": missing}) or []:
            tasks[row["id"]] = row
    return tasks

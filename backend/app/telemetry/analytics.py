from __future__ import annotations

from statistics import median
from typing import Any

from ..catalog import model_display_name, model_label
from .memory import elapsed_ms, memory_store


def _in_range(value: str | None, start: str | None, end: str | None) -> bool:
    if not value:
        return True
    if start and value < start:
        return False
    if end and value > end:
        return False
    return True


def _filtered_executions(installation_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    rows = memory_store.list_executions(installation_id)
    out = []
    for row in rows:
        if filters.get("provider") and row.get("provider") != filters["provider"]:
            continue
        if filters.get("model") and row.get("model_id") != filters["model"]:
            continue
        if filters.get("task_type"):
            task = memory_store.tasks.get(row.get("task_id") or "")
            if (task or {}).get("task_type") != filters["task_type"] and row.get("task_type") != filters["task_type"]:
                continue
        if filters.get("comparison_group_id") and row.get("comparison_group_id") != filters["comparison_group_id"]:
            continue
        if filters.get("outcome") and row.get("outcome") != filters["outcome"]:
            continue
        if filters.get("rag_enabled") is True:
            task = memory_store.tasks.get(row.get("task_id") or "")
            if not ((task or {}).get("rag_enabled") or row.get("rag_enabled")):
                continue
        if filters.get("has_tool_calls") and int(row.get("tool_call_count") or 0) == 0:
            continue
        if filters.get("has_retries") and int(row.get("retry_count") or 0) == 0:
            continue
        if not _in_range(row.get("started_at"), filters.get("start"), filters.get("end")):
            continue
        out.append(row)
    return out


def _task_for(execution: dict[str, Any]) -> dict[str, Any]:
    return memory_store.tasks.get(execution.get("task_id") or "") or {}


def fingerprint(execution: dict[str, Any]) -> dict[str, Any]:
    llm_rows = memory_store.llm_for(execution["id"])
    input_tokens = sum(row.get("input_tokens") or 0 for row in llm_rows if row.get("input_tokens") is not None)
    output_tokens = sum(row.get("output_tokens") or 0 for row in llm_rows if row.get("output_tokens") is not None)
    cached_tokens = sum(row.get("cached_tokens") or 0 for row in llm_rows if row.get("cached_tokens") is not None)
    total_tokens = sum(row.get("total_tokens") or 0 for row in llm_rows if row.get("total_tokens") is not None)
    usage_available = any(row.get("usage_available") for row in llm_rows)
    cost_values = [row.get("estimated_cost_usd") for row in llm_rows if row.get("estimated_cost_usd") is not None]
    priced = [row for row in llm_rows if row.get("estimated_cost_usd") is not None]
    return {
        "execution_id": execution["id"],
        "model": model_label(execution.get("provider") or "", execution.get("model_id") or ""),
        "model_id": execution.get("model_id"),
        "display_name": model_display_name(execution.get("provider") or "", execution.get("model_id") or ""),
        "provider": execution.get("provider"),
        "task_type": _task_for(execution).get("task_type") or execution.get("task_type") or "general",
        "outcome": execution.get("outcome") or execution.get("status"),
        "llm_calls": execution.get("llm_call_count") or 0,
        "tool_calls": execution.get("tool_call_count") or 0,
        "files_touched": execution.get("files_touched_count") or 0,
        "rag_calls": execution.get("rag_query_count") or 0,
        "retries": execution.get("retry_count") or 0,
        "duration_ms": execution.get("duration_ms")
        if execution.get("duration_ms") is not None
        else elapsed_ms(execution.get("started_at")),
        "input_tokens": input_tokens if usage_available else None,
        "output_tokens": output_tokens if usage_available else None,
        "cached_tokens": cached_tokens if usage_available else None,
        "total_tokens": total_tokens if usage_available else None,
        "estimated_cost_usd": sum(cost_values) if cost_values else None,
        "pricing_coverage": (len(priced) / len(llm_rows)) if llm_rows else None,
        "status": execution.get("status"),
    }


def execution_detail(execution_id: str) -> dict[str, Any] | None:
    execution = memory_store.get_execution(execution_id)
    if not execution:
        return None
    llm_rows = memory_store.llm_for(execution_id)
    tool_rows = memory_store.tools_for(execution_id)
    rag_rows = memory_store.rag_for(execution_id)
    edit_rows = memory_store.edits_for(execution_id)
    successful_tools = [row for row in tool_rows if row.get("status") == "success"]
    latencies = [row.get("latency_ms") for row in tool_rows if row.get("latency_ms") is not None]
    fp = fingerprint(execution)
    output_tokens = fp.get("output_tokens")
    edits = execution.get("edit_count") or 0
    changed = (execution.get("lines_added") or 0) + (execution.get("lines_removed") or 0)
    cost = fp.get("estimated_cost_usd")
    return {
        "execution": execution,
        "task": _task_for(execution),
        "fingerprint": fp,
        "llm_events": llm_rows,
        "tool_events": tool_rows,
        "rag_events": rag_rows,
        "edit_events": edit_rows,
        "events": memory_store.events_for(execution_id),
        "code_impact": {
            "files_touched": execution.get("files_touched_count") or 0,
            "files_modified": execution.get("files_modified_count") or 0,
            "edits": edits,
            "lines_added": execution.get("lines_added") or 0,
            "lines_removed": execution.get("lines_removed") or 0,
            "output_tokens_per_edit": (output_tokens / edits) if output_tokens and edits else None,
            "cost_per_edit": (cost / edits) if cost is not None and edits else None,
            "cost_per_100_changed_lines": (cost / changed * 100) if cost is not None and changed else None,
            "source": "runtime_measured",
        },
        "workflow": {
            "time_to_first_edit_ms": execution.get("time_to_first_edit_ms"),
            "rework_loops": sum(1 for row in edit_rows if row.get("is_repeat_file_edit")),
            "correction_detected": execution.get("correction_detected"),
            "abandoned": execution.get("abandoned"),
            "source": "heuristic",
        },
        "tool_intelligence": {
            "tool_error_rate": (1 - len(successful_tools) / len(tool_rows)) if tool_rows else None,
            "median_tool_latency_ms": median(latencies) if latencies else None,
            "retry_count": execution.get("retry_count") or 0,
            "source": "runtime_measured",
        },
        "context": _context_metrics(rag_rows, llm_rows),
    }


def _context_metrics(rag_rows: list[dict[str, Any]], llm_rows: list[dict[str, Any]]) -> dict[str, Any]:
    retrieved = sum(row.get("estimated_retrieved_tokens") or 0 for row in rag_rows)
    selected = sum(row.get("context_selected_tokens") or 0 for row in rag_rows)
    sent = sum(row.get("input_tokens") or 0 for row in llm_rows if row.get("input_tokens") is not None)
    cached = sum(row.get("cached_tokens") or 0 for row in llm_rows if row.get("cached_tokens") is not None)
    utilization = None
    if selected and sent:
        utilization = sent / selected if selected else None
    cache_efficiency = (cached / sent) if sent else None
    return {
        "retrieved_tokens": retrieved or None,
        "selected_tokens": selected or None,
        "sent_tokens": sent or None,
        "cached_tokens": cached or None,
        "utilization": utilization,
        "cache_efficiency": cache_efficiency,
        "source": "calculated",
    }


def overview(installation_id: str, filters: dict[str, Any]) -> dict[str, Any]:
    executions = _filtered_executions(installation_id, filters)
    llm_rows = [row for execution in executions for row in memory_store.llm_for(execution["id"])]
    tool_rows = [row for execution in executions for row in memory_store.tools_for(execution["id"])]
    durations = [row.get("duration_ms") for row in executions if row.get("duration_ms") is not None]
    costs = [row.get("estimated_cost_usd") for row in llm_rows if row.get("estimated_cost_usd") is not None]
    tokens = [row.get("total_tokens") for row in llm_rows if row.get("total_tokens") is not None]
    priced_llm = [row for row in llm_rows if row.get("estimated_cost_usd") is not None]
    successful_tools = [row for row in tool_rows if row.get("status") == "success"]
    return {
        "executions": len(executions),
        "llm_calls": len(llm_rows),
        "total_tokens": sum(tokens) if tokens else None,
        "estimated_cost_usd": sum(costs) if costs else None,
        "median_duration_ms": median(durations) if durations else None,
        "tool_calls": len(tool_rows),
        "tool_success_rate": (len(successful_tools) / len(tool_rows)) if tool_rows else None,
        "pricing_coverage": (len(priced_llm) / len(llm_rows)) if llm_rows else None,
        "source_notes": {
            "tokens": "provider_reported",
            "cost": "calculated",
            "duration": "runtime_measured",
        },
    }


def model_analytics(installation_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    executions = _filtered_executions(installation_id, filters)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in executions:
        grouped.setdefault(f"{row.get('provider')}:{row.get('model_id')}", []).append(row)
    profiles = []
    for key, rows in grouped.items():
        provider, model_id = key.split(":", 1)
        llm_rows = [item for execution in rows for item in memory_store.llm_for(execution["id"])]
        tool_rows = [item for execution in rows for item in memory_store.tools_for(execution["id"])]
        durations = [row.get("duration_ms") for row in rows if row.get("duration_ms") is not None]
        costs = [item.get("estimated_cost_usd") for item in llm_rows if item.get("estimated_cost_usd") is not None]
        tokens = [item.get("total_tokens") for item in llm_rows if item.get("total_tokens") is not None]
        successful = [row for row in rows if row.get("outcome") == "success"]
        successful_tools = [item for item in tool_rows if item.get("status") == "success"]
        completed = [row for row in rows if row.get("status") in {"completed", "failed"}]
        profiles.append(
            {
                "provider": provider,
                "model_id": model_id,
                "display_name": model_display_name(provider, model_id),
                "display_label": model_label(provider, model_id),
                "runs": len(rows),
                "observed_success_rate": (len(successful) / len(completed)) if completed else None,
                "median_duration_ms": median(durations) if durations else None,
                "average_tokens": (sum(tokens) / len(tokens)) if tokens else None,
                "average_cost_usd": (sum(costs) / len(rows)) if costs else None,
                "average_tool_calls": (sum(row.get("tool_call_count") or 0 for row in rows) / len(rows)) if rows else None,
                "tool_success_rate": (len(successful_tools) / len(tool_rows)) if tool_rows else None,
                "label": "Based on your observed runs.",
            }
        )
    return profiles


def tool_analytics(installation_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    executions = _filtered_executions(installation_id, filters)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for execution in executions:
        for row in memory_store.tools_for(execution["id"]):
            grouped.setdefault(row["tool_name"], []).append(row)
    out = []
    for name, rows in grouped.items():
        success = [row for row in rows if row.get("status") == "success"]
        retries = sum(int(row.get("retry_no") or 0) > 0 for row in rows)
        latencies = [row.get("latency_ms") for row in rows if row.get("latency_ms") is not None]
        out.append(
            {
                "tool_name": name,
                "calls": len(rows),
                "successful": len(success),
                "failed": len(rows) - len(success),
                "retries": retries,
                "success_rate": len(success) / len(rows) if rows else None,
                "average_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
                "median_latency_ms": median(latencies) if latencies else None,
            }
        )
    out.sort(key=lambda item: item["calls"], reverse=True)
    return out


def history(installation_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for execution in _filtered_executions(installation_id, filters):
        fp = fingerprint(execution)
        task = _task_for(execution)
        task_text = task.get("task_text") or execution.get("task_text") or ""
        rows.append(
            {
                **fp,
                "started_at": execution.get("started_at"),
                "task_preview": task_text[:140],
                "task_text": task_text,
                "final_output": execution.get("final_output"),
                "comparison_group_id": execution.get("comparison_group_id"),
                "rag_enabled": bool(task.get("rag_enabled") or execution.get("rag_enabled")),
            }
        )
    return rows


def comparison(installation_id: str, comparison_group_id: str) -> dict[str, Any]:
    group = memory_store.comparison_groups.get(comparison_group_id)
    executions = [
        row
        for row in memory_store.list_executions(installation_id)
        if row.get("comparison_group_id") == comparison_group_id
    ]
    details = []
    for execution in executions:
        detail = execution_detail(execution["id"])
        if detail:
            details.append(detail)
    metrics = [
        "model",
        "outcome",
        "duration_ms",
        "llm_calls",
        "tool_calls",
        "retries",
        "input_tokens",
        "output_tokens",
        "cached_tokens",
        "total_tokens",
        "estimated_cost_usd",
        "files_touched",
        "rag_calls",
    ]
    table = []
    for metric in metrics:
        table.append(
            {
                "metric": metric,
                "runs": [item["fingerprint"].get(metric) if metric != "model" else item["fingerprint"].get("model") for item in details],
            }
        )
    extra = [
        {
            "metric": "tool_success_rate",
            "runs": [
                None
                if not item["tool_events"]
                else sum(1 for row in item["tool_events"] if row.get("status") == "success") / len(item["tool_events"])
                for item in details
            ],
        },
        {
            "metric": "tests_passed",
            "runs": [item["execution"].get("tests_passed") for item in details],
        },
        {
            "metric": "time_to_first_edit_ms",
            "runs": [item["workflow"].get("time_to_first_edit_ms") for item in details],
        },
        {
            "metric": "lines_added",
            "runs": [item["code_impact"].get("lines_added") for item in details],
        },
        {
            "metric": "lines_removed",
            "runs": [item["code_impact"].get("lines_removed") for item in details],
        },
    ]
    return {
        "group": group,
        "executions": [item["fingerprint"] for item in details],
        "details": details,
        "table": table + extra,
        "note": "Observed differences. AgentLens does not declare a winner.",
    }

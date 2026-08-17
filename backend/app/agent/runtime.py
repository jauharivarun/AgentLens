from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from ..config import get_settings
from ..gateway.llm_gateway import LLMGateway
from ..rag.service import rag_search as rag_search_service
from ..telemetry.recorder import recorder
from . import tools
from .control import is_stop_requested

SYSTEM_PROMPT = """You are AgentLens, a tool-using assistant in the demo workspace sample_workspace/. Uploaded files live in uploads/. Knowledge markdown is searchable with rag_search.

Tool policy:
- Knowledge or policy questions: rag_search, then cite source filenames. Do not invent document contents.
- Spreadsheet or CSV questions: preview_csv first. Use read_file only if you need more than the preview.
- Coding: list_files or read_file before write_file. After edits, run_tests. Use run_command only for other allowlisted python.
- User-attached files: list_files/read_file (or preview_csv) under uploads/.
- Inspect before you edit. Do not wait for a task-type setting.

Output:
- Numbered answers must match the user's numbering (1, 2, 3…).
- Short headings as titles. No decorative --- rules or walls of asterisks.
- Keep answers concise and concrete.

When the task is done, give the final answer and do not call more tools.
"""


def _tool_message(call_id: str, payload: Any) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, default=str)
    if len(text) > 8000:
        text = text[:8000] + "...[truncated]"
    return {"role": "tool", "tool_call_id": call_id, "content": text}


async def _execute_tool(name: str, arguments: dict[str, Any], execution_id: str) -> tuple[Any, dict[str, Any], str]:
    if name == "list_files":
        result = tools.list_files(arguments.get("path"))
        return result, {"count": result.get("count")}, "success"
    if name == "read_file":
        result = tools.read_file(
            arguments.get("path") or arguments.get("relative_path"),
            arguments.get("start_line"),
            arguments.get("end_line"),
        )
        return result, {"path": result.get("path"), "bytes": result.get("bytes")}, "success"
    if name == "search_files":
        result = tools.search_files(arguments.get("query", ""), arguments.get("path"))
        return result, {"count": result.get("count")}, "success"
    if name == "write_file":
        result = tools.write_file(arguments.get("path"), arguments.get("content", ""))
        execution = recorder.store.get_execution(execution_id)
        touched = list((execution or {}).get("files_touched") or [])
        is_repeat = result["path"] in touched
        await recorder.record_edit_event(
            execution_id=execution_id,
            file_path=result["path"],
            operation=result["operation"],
            lines_added=result["lines_added"],
            lines_removed=result["lines_removed"],
            content_size_before=result["content_size_before"],
            content_size_after=result["content_size_after"],
            is_repeat=is_repeat,
        )
        return result, {"path": result["path"], "lines_added": result["lines_added"], "lines_removed": result["lines_removed"]}, "success"
    if name == "run_command":
        result = tools.run_command(arguments.get("command", ""))
        execution = recorder.store.get_execution(execution_id)
        if execution and result.get("tests_run"):
            execution["tests_run"] = int(execution.get("tests_run") or 0) + int(result["tests_run"])
            execution["tests_passed"] = int(execution.get("tests_passed") or 0) + int(result.get("tests_passed") or 0)
        status = "success" if result.get("exit_code") == 0 else "failed"
        return result, {"exit_code": result.get("exit_code"), "tests_passed": result.get("tests_passed")}, status
    if name == "preview_csv":
        result = tools.preview_csv(arguments.get("path") or "", int(arguments.get("rows") or 8))
        return result, {"path": result.get("path"), "preview_rows": result.get("preview_rows"), "row_count": result.get("row_count")}, "success"
    if name == "run_tests":
        result = tools.run_tests(arguments.get("path"))
        execution = recorder.store.get_execution(execution_id)
        if execution and result.get("tests_run"):
            execution["tests_run"] = int(execution.get("tests_run") or 0) + int(result["tests_run"])
            execution["tests_passed"] = int(execution.get("tests_passed") or 0) + int(result.get("tests_passed") or 0)
        status = "success" if result.get("exit_code") == 0 else "failed"
        return result, {"target": result.get("target"), "exit_code": result.get("exit_code"), "tests_passed": result.get("tests_passed")}, status
    if name == "rag_search":
        result = await rag_search_service(arguments.get("query", ""), int(arguments.get("top_k") or 4))
        await recorder.record_rag_event(
            execution_id=execution_id,
            payload={
                "query_hash": result["query_hash"],
                "top_k": result["top_k"],
                "result_count": result["result_count"],
                "retrieval_latency_ms": result["retrieval_latency_ms"],
                "retrieved_chunk_count": result["retrieved_chunk_count"],
                "estimated_retrieved_tokens": result["estimated_retrieved_tokens"],
                "context_selected_tokens": result["context_selected_tokens"],
                "metadata": result["metadata"],
            },
        )
        slim = {
            "results": [
                {
                    "chunk_id": item["chunk_id"],
                    "document": item["document"],
                    "source": item["source"],
                    "text": item["text"],
                    "score": item.get("score"),
                }
                for item in result["results"]
            ],
            "result_count": result["result_count"],
            "backend": result["backend"],
        }
        return slim, {"result_count": result["result_count"], "backend": result["backend"]}, "success"
    raise ValueError(f"Unknown tool: {name}")


async def run_agent(
    *,
    execution_id: str,
    task: str,
    provider: str,
    model_id: str,
    rag_enabled: bool,
    task_type: str,
) -> None:
    settings = get_settings()
    gateway = LLMGateway(telemetry=recorder)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    if rag_enabled:
        messages[0]["content"] += "\nThe user turned on knowledge search. Call rag_search before answering knowledge questions, and cite source filenames."

    max_iterations = settings.agent_max_iterations
    last_text = ""

    try:
        for iteration in range(1, max_iterations + 1):
            if is_stop_requested(execution_id):
                await recorder.stop_execution(execution_id, last_text or "Stopped by user.")
                return
            result, _cost = await gateway.generate(
                provider=provider,
                model=model_id,
                messages=messages,
                tools=tools.TOOL_DEFINITIONS,
                task_id=execution_id,
                execution_id=execution_id,
                sequence_no=iteration,
            )
            if is_stop_requested(execution_id):
                await recorder.stop_execution(execution_id, last_text or "Stopped by user.")
                return
            if result.status == "failed":
                if iteration < 3:
                    await recorder.record_execution_event(
                        execution_id,
                        "retry",
                        f"LLM call failed ({result.error_type}); retrying",
                        {"error_type": result.error_type},
                    )
                    continue
                await recorder.fail_execution(
                    execution_id,
                    result.raw_metadata.get("message")
                    or result.raw_metadata.get("error")
                    or result.error_type
                    or "The selected model provider could not complete the request.",
                )
                return

            assistant_payload: dict[str, Any] = {"role": "assistant", "content": result.text or ""}
            if result.tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in result.tool_calls
                ]
            messages.append(assistant_payload)

            if not result.tool_calls:
                last_text = result.text or ""
                await recorder.complete_execution(execution_id, last_text, outcome="success")
                return

            for call in result.tool_calls:
                if is_stop_requested(execution_id):
                    await recorder.stop_execution(execution_id, last_text or "Stopped by user.")
                    return
                input_meta = {k: v for k, v in call.arguments.items() if k != "content"}
                if "content" in call.arguments:
                    input_meta["content_chars"] = len(str(call.arguments.get("content") or ""))
                tool_row = await recorder.record_tool_start(
                    execution_id=execution_id,
                    tool_name=call.name,
                    input_metadata=input_meta,
                )
                started = time.perf_counter()
                status = "success"
                error_type = None
                output_meta: dict[str, Any] = {}
                payload: Any
                try:
                    payload, output_meta, status = await _execute_tool(call.name, call.arguments, execution_id)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    status = "failed"
                    error_type = exc.__class__.__name__
                    payload = {"error": str(exc), "error_type": error_type}
                    output_meta = payload
                latency_ms = int((time.perf_counter() - started) * 1000)
                await recorder.record_tool_complete(
                    tool_event_id=tool_row["id"],
                    execution_id=execution_id,
                    tool_name=call.name,
                    status=status,
                    latency_ms=latency_ms,
                    output_metadata=output_meta,
                    error_type=error_type,
                )
                messages.append(_tool_message(call.id, payload))

        await recorder.fail_execution(
            execution_id,
            "Stopped after the configured iteration limit without a final answer.",
            outcome="partial",
        )
    except asyncio.CancelledError:
        await recorder.stop_execution(execution_id, last_text or "Stopped by user.")

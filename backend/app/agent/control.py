from __future__ import annotations

import asyncio

_tasks: dict[str, asyncio.Task] = {}
_stop_requested: set[str] = set()


def register_run(execution_id: str, task: asyncio.Task) -> None:
    _stop_requested.discard(execution_id)
    _tasks[execution_id] = task


def request_stop(execution_id: str) -> bool:
    _stop_requested.add(execution_id)
    task = _tasks.get(execution_id)
    if task and not task.done():
        task.cancel()
        return True
    return execution_id in _stop_requested


def is_stop_requested(execution_id: str) -> bool:
    return execution_id in _stop_requested


def clear_run(execution_id: str) -> None:
    _tasks.pop(execution_id, None)
    _stop_requested.discard(execution_id)

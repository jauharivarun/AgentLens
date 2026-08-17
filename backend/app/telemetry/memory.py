from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def elapsed_ms(started_at: str | None, ended: datetime | None = None) -> int | None:
    if not started_at:
        return None
    try:
        start = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        end = ended or utcnow()
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return max(0, int((end - start).total_seconds() * 1000))
    except (TypeError, ValueError):
        return None


class MemoryStore:
    """In-process store used for live polling and as a fallback when Supabase is unset."""

    def __init__(self) -> None:
        self.installations: dict[str, dict[str, Any]] = {}
        self.workspaces: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.comparison_groups: dict[str, dict[str, Any]] = {}
        self.executions: dict[str, dict[str, Any]] = {}
        self.llm_events: list[dict[str, Any]] = []
        self.tool_events: list[dict[str, Any]] = []
        self.rag_events: list[dict[str, Any]] = []
        self.execution_events: list[dict[str, Any]] = []
        self.edit_events: list[dict[str, Any]] = []

    def upsert_installation(self, installation_id: str) -> None:
        now = iso(utcnow())
        existing = self.installations.get(installation_id)
        if existing:
            existing["last_seen_at"] = now
            return
        self.installations[installation_id] = {
            "id": installation_id,
            "created_at": now,
            "last_seen_at": now,
            "metadata": {},
        }

    def ensure_workspace(self, installation_id: str, workspace_id: str, name: str = "Demo workspace") -> dict[str, Any]:
        existing = self.workspaces.get(workspace_id)
        if existing:
            return existing
        row = {
            "id": workspace_id,
            "installation_id": installation_id,
            "name": name,
            "type": "demo",
            "created_at": iso(utcnow()),
            "metadata": {},
        }
        self.workspaces[workspace_id] = row
        return row

    def insert_task(self, row: dict[str, Any]) -> dict[str, Any]:
        self.tasks[row["id"]] = row
        return row

    def insert_comparison_group(self, row: dict[str, Any]) -> dict[str, Any]:
        self.comparison_groups[row["id"]] = row
        return row

    def list_comparison_groups(self, installation_id: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self.comparison_groups.values()
            if row["installation_id"] == installation_id
        ]

    def insert_execution(self, row: dict[str, Any]) -> dict[str, Any]:
        self.executions[row["id"]] = row
        return row

    def update_execution(self, execution_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        row = self.executions.get(execution_id)
        if not row:
            return None
        row.update(patch)
        return row

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        return self.executions.get(execution_id)

    def list_executions(self, installation_id: str) -> list[dict[str, Any]]:
        rows = [row for row in self.executions.values() if row["installation_id"] == installation_id]
        rows.sort(key=lambda item: item.get("started_at") or "", reverse=True)
        return rows

    def append_llm(self, row: dict[str, Any]) -> None:
        self.llm_events.append(row)

    def append_tool(self, row: dict[str, Any]) -> None:
        self.tool_events.append(row)

    def append_rag(self, row: dict[str, Any]) -> None:
        self.rag_events.append(row)

    def append_event(self, row: dict[str, Any]) -> None:
        self.execution_events.append(row)

    def append_edit(self, row: dict[str, Any]) -> None:
        self.edit_events.append(row)

    def events_for(self, execution_id: str) -> list[dict[str, Any]]:
        rows = [row for row in self.execution_events if row["execution_id"] == execution_id]
        rows.sort(key=lambda item: item.get("sequence_no") or 0)
        return rows

    def llm_for(self, execution_id: str) -> list[dict[str, Any]]:
        return [row for row in self.llm_events if row["execution_id"] == execution_id]

    def tools_for(self, execution_id: str) -> list[dict[str, Any]]:
        return [row for row in self.tool_events if row["execution_id"] == execution_id]

    def rag_for(self, execution_id: str) -> list[dict[str, Any]]:
        return [row for row in self.rag_events if row["execution_id"] == execution_id]

    def edits_for(self, execution_id: str) -> list[dict[str, Any]]:
        return [row for row in self.edit_events if row["execution_id"] == execution_id]


memory_store = MemoryStore()

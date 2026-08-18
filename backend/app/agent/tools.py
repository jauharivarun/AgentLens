from __future__ import annotations

import csv
import difflib
import io
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from ..config import get_settings

MAX_FILE_BYTES = 80_000
MAX_OUTPUT_CHARS = 12_000
COMMAND_TIMEOUT_SEC = 20

ALLOWED_COMMAND_PREFIXES = (
    ("python", "-m", "pytest"),
    ("python3", "-m", "pytest"),
    ("python", "-m", "unittest"),
    ("python3", "-m", "unittest"),
    ("python",),
    ("python3",),
)

ALLOWED_MODULES = {"pytest", "unittest"}

BLOCKED_TOKENS = {
    "rm",
    "sudo",
    "chmod",
    "chown",
    "curl",
    "wget",
    "nc",
    "ssh",
    "scp",
    "env",
    "printenv",
    "export",
    "kill",
    "reboot",
    "shutdown",
}


def workspace_root() -> Path:
    return get_settings().workspace_dir


def resolve_workspace_path(relative: str | None = None) -> Path:
    root = workspace_root()
    if not relative or relative in {".", "./"}:
        return root
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise ValueError("Path is outside the designated workspace")
    return candidate


def line_diff(old: str, new: str) -> tuple[int, int]:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines)
    added = 0
    removed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            removed += i2 - i1
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "insert":
            added += j2 - j1
    return added, removed


def list_files(path: str | None = None) -> dict[str, Any]:
    root = resolve_workspace_path(path)
    files: list[str] = []
    for item in sorted(root.rglob("*")):
        if item.is_file() and ".git" not in item.parts:
            files.append(str(item.relative_to(workspace_root())))
    return {"files": files, "count": len(files)}


def read_file(relative_path: str, start_line: int | None = None, end_line: int | None = None) -> dict[str, Any]:
    path = resolve_workspace_path(relative_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    if len(raw.encode("utf-8")) > MAX_FILE_BYTES:
        raw = raw[:MAX_FILE_BYTES] + "\n...[truncated]"
    lines = raw.splitlines()
    if start_line is not None or end_line is not None:
        start = max((start_line or 1) - 1, 0)
        end = end_line if end_line is not None else len(lines)
        lines = lines[start:end]
        raw = "\n".join(lines)
    if len(raw) > MAX_OUTPUT_CHARS:
        raw = raw[:MAX_OUTPUT_CHARS] + "\n...[truncated]"
    return {
        "path": relative_path,
        "content": raw,
        "line_count": len(lines),
        "bytes": path.stat().st_size,
    }


def preview_csv(relative_path: str, rows: int = 8) -> dict[str, Any]:
    path = resolve_workspace_path(relative_path)
    if path.suffix.lower() != ".csv":
        raise ValueError("preview_csv only accepts .csv files")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_path)
    limit = max(1, min(int(rows or 8), 30))
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    all_rows = list(reader)
    if not all_rows:
        return {"path": relative_path, "headers": [], "rows": [], "row_count": 0, "preview_rows": 0, "truncated": False}
    headers = all_rows[0]
    body = all_rows[1:]
    preview = body[:limit]
    return {
        "path": relative_path,
        "headers": headers,
        "rows": preview,
        "row_count": len(body),
        "preview_rows": len(preview),
        "truncated": len(body) > len(preview),
    }


def run_tests(path: str | None = None) -> dict[str, Any]:
    target = path.strip() if path and path.strip() else "tests"
    resolve_workspace_path(target)
    result = run_command(f"python -m pytest {shlex.quote(target)} -q")
    result["tool"] = "run_tests"
    result["target"] = target
    return result


def search_files(query: str, path: str | None = None) -> dict[str, Any]:
    root = resolve_workspace_path(path)
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches: list[dict[str, Any]] = []
    for item in root.rglob("*"):
        if not item.is_file() or item.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pyc"}:
            continue
        try:
            text = item.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                matches.append(
                    {
                        "path": str(item.relative_to(workspace_root())),
                        "line": idx,
                        "snippet": line.strip()[:240],
                    }
                )
                if len(matches) >= 40:
                    return {"matches": matches, "count": len(matches), "truncated": True}
    return {"matches": matches, "count": len(matches), "truncated": False}


def write_file(relative_path: str, content: str) -> dict[str, Any]:
    path = resolve_workspace_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    path.write_text(content, encoding="utf-8")
    added, removed = line_diff(old, content)
    return {
        "path": relative_path,
        "status": "written",
        "operation": "update" if old else "write",
        "lines_added": added,
        "lines_removed": removed,
        "content_size_before": len(old),
        "content_size_after": len(content),
        "existed": bool(old),
    }


def _command_allowed(parts: list[str]) -> bool:
    if not parts:
        return False
    lowered = [part.lower() for part in parts]
    if any(token in BLOCKED_TOKENS for token in lowered):
        return False
    for prefix in ALLOWED_COMMAND_PREFIXES:
        if lowered[: len(prefix)] == list(prefix):
            if prefix in {("python",), ("python3",)}:
                script = parts[1] if len(parts) > 1 else ""
                if script.startswith("-") and script not in {"-m"}:
                    return False
                if script == "-m":
                    module = parts[2] if len(parts) > 2 else ""
                    if module.lower() not in ALLOWED_MODULES:
                        return False
                if script and not script.startswith("-"):
                    try:
                        resolve_workspace_path(script)
                    except ValueError:
                        return False
            return True
    return False


def run_command(command: str) -> dict[str, Any]:
    parts = shlex.split(command)
    if not _command_allowed(parts):
        raise PermissionError("Command is not on the allowlist")
    completed = subprocess.run(
        parts,
        cwd=workspace_root(),
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SEC,
        check=False,
    )
    stdout = (completed.stdout or "")[:MAX_OUTPUT_CHARS]
    stderr = (completed.stderr or "")[:MAX_OUTPUT_CHARS]
    tests_run = None
    tests_passed = None
    summary = re.search(r"(\d+) passed", stdout + stderr)
    failed = re.search(r"(\d+) failed", stdout + stderr)
    if summary:
        tests_passed = int(summary.group(1))
        tests_run = tests_passed + (int(failed.group(1)) if failed else 0)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "status": "success" if completed.returncode == 0 else "failed",
        "tests_run": tests_run,
        "tests_passed": tests_passed,
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the demo workspace. Returns relative paths only.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Optional relative subdirectory"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the demo workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search workspace files for a text query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or update a file in the demo workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run an allowlisted command in the demo workspace. Python tests and python scripts only.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "preview_csv",
            "description": "Preview the header and first rows of a CSV file in the demo workspace. Use this instead of reading the whole file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to a .csv file"},
                    "rows": {"type": "integer", "description": "How many data rows to return (1-30, default 8)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run pytest in the demo workspace. Prefer this over run_command for tests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Optional tests path, default tests"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Search the knowledge base and return relevant chunks with sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    },
]

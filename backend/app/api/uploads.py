from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..agent.tools import workspace_root
from ..rag.service import ingest_knowledge

router = APIRouter()

ALLOWED_SUFFIXES = {".md", ".txt", ".csv", ".json", ".py"}
MAX_BYTES = 2_000_000


def _safe_name(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    if not cleaned:
        raise HTTPException(status_code=400, detail="Invalid file name")
    suffix = Path(cleaned).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Use a text file: .md, .txt, .csv, .json, or .py",
        )
    return cleaned


def uploads_dir() -> Path:
    path = workspace_root() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.get("/api/uploads")
async def list_uploads() -> dict:
    folder = uploads_dir()
    files = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.name != ".gitkeep":
            files.append({"name": path.name, "path": f"uploads/{path.name}", "bytes": path.stat().st_size})
    return {"files": files}


@router.post("/api/uploads")
async def upload_file(file: UploadFile = File(...)) -> dict:
    filename = _safe_name(file.filename or "upload.txt")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File is larger than 2 MB")
    dest = uploads_dir() / filename
    dest.write_bytes(raw)
    ingest = await ingest_knowledge()
    return {
        "name": filename,
        "path": f"uploads/{filename}",
        "bytes": dest.stat().st_size,
        "ingest": ingest,
    }

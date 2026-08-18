from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..agent.tools import workspace_root
from ..rag.service import ingest_knowledge, list_knowledge_catalog

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


def _reject_traversal(name: str) -> None:
    if not name or name in {".", ".."} or "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid file name")


def uploads_dir() -> Path:
    path = workspace_root() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _upload_path(name: str) -> Path:
    _reject_traversal(name)
    filename = _safe_name(name)
    folder = uploads_dir().resolve()
    dest = (folder / filename).resolve()
    if folder not in dest.parents and dest != folder:
        raise HTTPException(status_code=400, detail="Path is outside uploads")
    if dest.parent != folder:
        raise HTTPException(status_code=400, detail="Path is outside uploads")
    return dest


@router.get("/api/uploads")
async def list_uploads() -> dict:
    catalog = list_knowledge_catalog()
    return {
        "files": catalog["uploads"],
        "uploads": catalog["uploads"],
        "builtin": catalog["builtin"],
    }


@router.post("/api/uploads")
async def upload_file(file: UploadFile = File(...)) -> dict:
    filename = _safe_name(file.filename or "upload.txt")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File is larger than 2 MB")
    dest = _upload_path(filename)
    dest.write_bytes(raw)
    ingest = await ingest_knowledge()
    return {
        "name": filename,
        "path": f"uploads/{filename}",
        "bytes": dest.stat().st_size,
        "ingest": ingest,
    }


@router.delete("/api/uploads/{name}")
async def delete_upload(name: str) -> dict:
    dest = _upload_path(name)
    if dest.name == ".gitkeep" or not dest.is_file():
        raise HTTPException(status_code=404, detail="Upload not found")
    dest.unlink()
    ingest = await ingest_knowledge()
    return {"deleted": dest.name, "path": f"uploads/{dest.name}", "ingest": ingest}

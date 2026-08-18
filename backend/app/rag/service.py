from __future__ import annotations

import logging
import math
import re
import time
from pathlib import Path
from typing import Any

from ..config import ROOT_DIR, get_settings
from ..telemetry.recorder import query_hash

logger = logging.getLogger(__name__)

COLLECTION_NAME = "agentlens_demo"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120


def _split_chunks(text: str) -> list[str]:
    paragraphs = re.split(r"\n{2,}", text)
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}".strip() if buf else para.strip()
        if len(candidate) < CHUNK_SIZE:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        buf = para.strip()
    if buf:
        chunks.append(buf)

    refined: list[str] = []
    for chunk in chunks:
        if len(chunk) <= CHUNK_SIZE:
            refined.append(chunk)
            continue
        start = 0
        while start < len(chunk):
            refined.append(chunk[start : start + CHUNK_SIZE])
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return [item for item in refined if item.strip()]


def knowledge_files() -> list[Path]:
    workspace = get_settings().workspace_dir
    files: list[Path] = []
    for folder in (workspace / "knowledge", workspace / "uploads"):
        if not folder.exists():
            continue
        for ext in ("*.md", "*.txt", "*.csv", "*.json", "*.py"):
            files.extend(folder.glob(ext))
    return sorted({path.resolve() for path in files if path.is_file()})


def _local_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for path in knowledge_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for idx, chunk in enumerate(_split_chunks(text)):
            docs.append(
                {
                    "id": f"{path.stem}-{idx}",
                    "document_id": path.stem,
                    "filename": path.name,
                    "chunk_index": idx,
                    "text": chunk,
                    "source": str(path.relative_to(ROOT_DIR)),
                }
            )
    return docs


def _keyword_score(query: str, text: str) -> float:
    q = {token.lower() for token in re.findall(r"[a-zA-Z0-9]+", query) if len(token) > 2}
    if not q:
        return 0.0
    t = {token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)}
    if not t:
        return 0.0
    return len(q & t) / math.sqrt(len(q) * len(t))


async def _embed(texts: list[str]) -> list[list[float]] | None:
    settings = get_settings()
    if not settings.openai_configured:
        return None
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(model=settings.openai_embedding_model, input=texts)
        return [item.embedding for item in response.data]
    except Exception as exc:
        logger.warning("Embedding failed: %s", exc)
        return None


def _chroma_collection():
    settings = get_settings()
    if not settings.chroma_configured:
        return None
    try:
        import chromadb

        client = chromadb.CloudClient(
            api_key=settings.chroma_api_key,
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
        )
        return client.get_or_create_collection(COLLECTION_NAME)
    except Exception as exc:
        logger.warning("Chroma Cloud unavailable: %s", exc)
        return None


_memory_index: list[dict[str, Any]] = []


def list_knowledge_catalog() -> dict[str, list[dict[str, Any]]]:
    workspace = get_settings().workspace_dir
    uploads: list[dict[str, Any]] = []
    builtin: list[dict[str, Any]] = []
    for path in knowledge_files():
        try:
            rel = path.relative_to(workspace).as_posix()
        except ValueError:
            rel = path.name
        item = {"name": path.name, "path": rel, "bytes": path.stat().st_size}
        if path.parent.name == "uploads":
            uploads.append(item)
        else:
            builtin.append(item)
    return {"uploads": uploads, "builtin": builtin}


def _prune_chroma(collection: Any, keep_ids: set[str]) -> int:
    try:
        existing = collection.get(include=[])
        stale = [item for item in (existing.get("ids") or []) if item not in keep_ids]
        if stale:
            collection.delete(ids=stale)
        return len(stale)
    except Exception as exc:
        logger.warning("Chroma prune failed: %s", exc)
        return 0


def _reset_memory_index(docs: list[dict[str, Any]], embeddings: list[list[float]] | None) -> None:
    global _memory_index
    _memory_index = []
    for doc, embedding in zip(docs, embeddings or [None] * len(docs)):
        item = dict(doc)
        item["embedding"] = embedding
        _memory_index.append(item)


async def ingest_knowledge() -> dict[str, Any]:
    docs = _local_documents()
    keep_ids = {doc["id"] for doc in docs}
    collection = _chroma_collection()

    if not docs:
        if collection is not None:
            _prune_chroma(collection, set())
        _reset_memory_index([], None)
        return {"status": "empty", "chunks": 0, "backend": "none"}

    embeddings = await _embed([doc["text"] for doc in docs])
    if collection is not None and embeddings is not None:
        collection.upsert(
            ids=[doc["id"] for doc in docs],
            documents=[doc["text"] for doc in docs],
            embeddings=embeddings,
            metadatas=[
                {
                    "document_id": doc["document_id"],
                    "filename": doc["filename"],
                    "chunk_index": doc["chunk_index"],
                    "source": doc["source"],
                }
                for doc in docs
            ],
        )
        pruned = _prune_chroma(collection, keep_ids)
        return {"status": "ok", "chunks": len(docs), "pruned": pruned, "backend": "chroma_cloud"}

    _reset_memory_index(docs, embeddings)
    if collection is not None:
        _prune_chroma(collection, keep_ids)
    return {
        "status": "ok",
        "chunks": len(docs),
        "backend": "memory_embeddings" if embeddings else "memory_keyword",
    }


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if den == 0:
        return 0.0
    return num / den


async def rag_search(query: str, top_k: int = 4) -> dict[str, Any]:
    started = time.perf_counter()
    top_k = max(1, min(top_k, 8))
    collection = _chroma_collection()
    embeddings = await _embed([query])
    results: list[dict[str, Any]] = []
    backend = "none"

    if collection is not None and embeddings is not None:
        backend = "chroma_cloud"
        raw = collection.query(query_embeddings=embeddings, n_results=top_k)
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        ids = (raw.get("ids") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        for idx, text in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            results.append(
                {
                    "chunk_id": ids[idx] if idx < len(ids) else f"chunk-{idx}",
                    "document": meta.get("filename"),
                    "source": meta.get("source"),
                    "text": text,
                    "score": None if idx >= len(distances) else distances[idx],
                }
            )
    else:
        docs = _memory_index or _local_documents()
        if embeddings and docs and docs[0].get("embedding"):
            backend = "memory_embeddings"
            scored = []
            for doc in docs:
                if not doc.get("embedding"):
                    continue
                scored.append((_cosine(embeddings[0], doc["embedding"]), doc))
            scored.sort(key=lambda item: item[0], reverse=True)
            for score, doc in scored[:top_k]:
                results.append(
                    {
                        "chunk_id": doc["id"],
                        "document": doc["filename"],
                        "source": doc["source"],
                        "text": doc["text"],
                        "score": score,
                    }
                )
        else:
            backend = "memory_keyword"
            scored = [(_keyword_score(query, doc["text"]), doc) for doc in docs]
            scored.sort(key=lambda item: item[0], reverse=True)
            for score, doc in scored[:top_k]:
                if score <= 0:
                    continue
                results.append(
                    {
                        "chunk_id": doc["id"],
                        "document": doc["filename"],
                        "source": doc["source"],
                        "text": doc["text"],
                        "score": score,
                    }
                )

    latency_ms = int((time.perf_counter() - started) * 1000)
    retrieved_chars = sum(len(item.get("text") or "") for item in results)
    return {
        "query": query,
        "query_hash": query_hash(query),
        "top_k": top_k,
        "result_count": len(results),
        "retrieved_chunk_count": len(results),
        "retrieval_latency_ms": latency_ms,
        "estimated_retrieved_tokens": retrieved_chars // 4,
        "context_selected_tokens": retrieved_chars // 4,
        "backend": backend,
        "results": results,
        "metadata": {
            "documents": list({item.get("document") for item in results if item.get("document")}),
            "backend": backend,
        },
    }

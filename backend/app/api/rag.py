from fastapi import APIRouter

from ..rag.service import ingest_knowledge

router = APIRouter()


@router.post("/api/rag/ingest")
async def ingest() -> dict:
    return await ingest_knowledge()

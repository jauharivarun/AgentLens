from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/api/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "openai_configured": settings.openai_configured,
        "groq_configured": settings.groq_configured,
        "chroma_configured": settings.chroma_configured,
        "supabase_configured": settings.supabase_configured,
    }

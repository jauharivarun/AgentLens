from fastapi import APIRouter

from ..catalog import public_models

router = APIRouter()


@router.get("/api/models")
async def models() -> dict:
    return {"models": public_models()}

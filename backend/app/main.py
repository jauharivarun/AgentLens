from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.analytics import router as analytics_router
from .api.executions import router as executions_router
from .api.health import router as health_router
from .api.models import router as models_router
from .api.rag import router as rag_router
from .api.uploads import router as uploads_router
from .config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        from .rag.service import ingest_knowledge

        await ingest_knowledge()
    except Exception:
        pass
    yield


app = FastAPI(title="AgentLens", version="0.1.0", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(models_router)
app.include_router(executions_router)
app.include_router(analytics_router)
app.include_router(rag_router)
app.include_router(uploads_router)

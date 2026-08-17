from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Fill either file — same keys. backend/.env wins if both exist.
        env_file=(str(ROOT_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    groq_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    chroma_api_key: str = ""
    chroma_tenant: str = ""
    chroma_database: str = ""

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    agent_max_iterations: int = 12
    workspace_path: str = "sample_workspace"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def workspace_dir(self) -> Path:
        path = Path(self.workspace_path)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path.resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def chroma_configured(self) -> bool:
        return bool(self.chroma_api_key and self.chroma_tenant and self.chroma_database)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

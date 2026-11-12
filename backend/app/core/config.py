import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

def normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy 2.0 async compatibility."""
    if not url:
        return "sqlite+aiosqlite:///./repoverse.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

class Settings(BaseModel):
    PROJECT_NAME: str = "RepoVerse"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://repoverse.vercel.app",
    ]

    # Database
    DATABASE_URL: str = normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./repoverse.db")
    )

    # Ingestion & limits
    REPO_STORAGE_PATH: str = os.getenv("REPO_STORAGE_PATH", "./repoverse_repos")
    MAX_REPO_SIZE_MB: int = int(os.getenv("MAX_REPO_SIZE_MB", "150"))
    MAX_FILE_COUNT: int = int(os.getenv("MAX_FILE_COUNT", "3000"))
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", "1048576")) # 1MB per file
    CLONE_TIMEOUT_SECONDS: int = int(os.getenv("CLONE_TIMEOUT_SECONDS", "60"))

    # LLM & AI
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none") # none, openai, gemini, anthropic
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

settings = Settings()

# Ensure repository storage directory exists safely
try:
    Path(settings.REPO_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
except Exception:
    # Ephemeral fallback to /tmp
    settings.REPO_STORAGE_PATH = "/tmp/repoverse_repos"
    Path(settings.REPO_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

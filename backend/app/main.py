from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.logging import logger
from backend.app.api.routes import (
    health,
    repositories,
    architecture,
    symbols,
    codeflow,
    learning,
    chat,
    history,
    bookmarks,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    await init_db()
    yield
    logger.info("Shutting down RepoVerse...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RepoVerse: Interactive GitHub Repository Digital Twin & AI Code Understanding Platform",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allow all in development / configured origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register versioned API routers
api_prefix = settings.API_V1_STR
app.include_router(health.router, prefix=api_prefix, tags=["Health"])
app.include_router(repositories.router, prefix=api_prefix, tags=["Repositories"])
app.include_router(architecture.router, prefix=api_prefix, tags=["Architecture"])
app.include_router(symbols.router, prefix=api_prefix, tags=["Symbols"])
app.include_router(codeflow.router, prefix=api_prefix, tags=["CodeFlow"])
app.include_router(learning.router, prefix=api_prefix, tags=["Adaptive Learning"])
app.include_router(chat.router, prefix=api_prefix, tags=["Ask the Repository"])
app.include_router(history.router, prefix=api_prefix, tags=["Git Time Machine"])
app.include_router(bookmarks.router, prefix=api_prefix, tags=["Bookmarks"])

@app.get("/")
async def root():
    return {
        "message": "RepoVerse Engine Online",
        "tagline": "Understand Code. Explore Architecture. Travel Through Git History.",
        "docs": "/docs",
        "health": f"{api_prefix}/health",
    }

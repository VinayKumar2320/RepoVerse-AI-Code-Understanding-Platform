from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "parsing_support": ["python_ast", "tree_sitter_python", "tree_sitter_javascript", "tree_sitter_typescript"],
        "modes": ["beginner", "developer", "senior"],
        "storage": settings.REPO_STORAGE_PATH,
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from backend.app.core.database import get_db
from backend.app.models.entities import RepositorySnapshot
from backend.app.schemas.learning import AdaptiveExplanationResponse, TopicWalkthroughResponse
from backend.app.services.orchestrator import orchestrator
from backend.app.services.learning.adaptive_engine import AdaptiveLearningEngine

router = APIRouter()
learning_engine = AdaptiveLearningEngine()

@router.get("/repositories/{repo_id}/learning", response_model=AdaptiveExplanationResponse)
async def get_adaptive_learning(
    repo_id: str,
    level: str = Query("developer", description="beginner, developer, or senior"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found.")

    overview = orchestrator.overview_cache.get(snap.id)
    if not overview and snap.overview_json:
        from backend.app.schemas.repository import RepositoryOverview
        overview = RepositoryOverview(**snap.overview_json)

    if not overview:
        raise HTTPException(status_code=404, detail="Overview not generated.")

    graph_builder = orchestrator.graph_cache.get(snap.id)
    symbols = list(graph_builder.symbol_index.values()) if graph_builder else []
    analytics = orchestrator.analytics_service.compute_metrics(graph_builder.graph, snap.id) if graph_builder else None

    return learning_engine.generate_adaptive_explanation(
        level=level,
        overview=overview,
        symbols=symbols,
        analytics=analytics
    )

@router.get("/repositories/{repo_id}/learning/topic", response_model=TopicWalkthroughResponse)
async def get_topic_walkthrough(
    repo_id: str,
    topic: str = Query("api", description="authentication, api, database, testing, core_flow"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found.")

    overview = orchestrator.overview_cache.get(snap.id)
    if not overview:
        raise HTTPException(status_code=404, detail="Overview not found.")

    graph_builder = orchestrator.graph_cache.get(snap.id)
    symbols = list(graph_builder.symbol_index.values()) if graph_builder else []

    return learning_engine.generate_topic_walkthrough(topic, overview, symbols)

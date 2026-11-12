from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.database import get_db
from backend.app.models.entities import RepositorySnapshot
from backend.app.schemas.architecture import (
    ArchitectureGraphResponse, ArchitectureAnalyticsResponse,
    SimulationRequest, SimulationResponse
)
from backend.app.services.orchestrator import orchestrator
from backend.app.services.simulation.simulator import ArchitectureSimulator

router = APIRouter()
simulator = ArchitectureSimulator()

@router.get("/repositories/{repo_id}/architecture", response_model=ArchitectureGraphResponse)
async def get_architecture_graph(
    repo_id: str,
    level: int = Query(2, ge=1, le=3, description="1=Packages/Directories, 2=Modules/Files, 3=Symbols"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="No completed snapshot found.")

    graph_builder = orchestrator.graph_cache.get(snap.id)
    if not graph_builder:
        raise HTTPException(status_code=404, detail="Graph not loaded in active runtime cache.")

    nodes, edges = graph_builder.get_view_for_level(level)

    return ArchitectureGraphResponse(
        snapshot_id=snap.id,
        level=level,
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges)
    )

@router.get("/repositories/{repo_id}/analytics", response_model=ArchitectureAnalyticsResponse)
async def get_architecture_analytics(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="No completed snapshot found.")

    graph_builder = orchestrator.graph_cache.get(snap.id)
    if not graph_builder:
        raise HTTPException(status_code=404, detail="Graph not found in cache.")

    return orchestrator.analytics_service.compute_metrics(graph_builder.graph, snap.id)

@router.post("/repositories/{repo_id}/simulations", response_model=SimulationResponse)
async def run_architecture_simulation(
    repo_id: str,
    request: SimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="No completed snapshot found.")

    graph_builder = orchestrator.graph_cache.get(snap.id)
    if not graph_builder:
        raise HTTPException(status_code=404, detail="Graph not found.")

    return simulator.simulate_mutations(graph_builder.graph, snap.id, request)

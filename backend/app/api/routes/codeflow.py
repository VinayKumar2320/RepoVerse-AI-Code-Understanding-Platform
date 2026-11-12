from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from backend.app.core.database import get_db
from backend.app.models.entities import RepositorySnapshot
from backend.app.schemas.codeflow import CodeFlowTraceResponse
from backend.app.services.orchestrator import orchestrator
from backend.app.services.codeflow.tracer import CodeFlowTracer

router = APIRouter()
tracer = CodeFlowTracer()

@router.get("/repositories/{repo_id}/codeflow", response_model=CodeFlowTraceResponse)
async def get_code_flow_trace(
    repo_id: str,
    entry: Optional[str] = Query(None, description="Starting symbol name or endpoint"),
    depth: int = Query(5, ge=1, le=10),
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

    graph_builder = orchestrator.graph_cache.get(snap.id)
    if not graph_builder:
        raise HTTPException(status_code=404, detail="Graph not found in cache.")

    return tracer.trace_flow(
        nx_graph=graph_builder.graph,
        symbol_index=graph_builder.symbol_index,
        start_symbol_name_or_qname=entry or "",
        max_depth=depth
    )

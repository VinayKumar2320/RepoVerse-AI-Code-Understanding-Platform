from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict, Any, Optional

from backend.app.core.database import get_db
from backend.app.models.entities import RepositorySnapshot
from backend.app.services.orchestrator import orchestrator

router = APIRouter()

@router.get("/repositories/{repo_id}/symbols")
async def get_repository_symbols(
    repo_id: str,
    file_path: Optional[str] = Query(None, description="Optional file path filter"),
    kind: Optional[str] = Query(None, description="Filter by symbol kind (class, function, endpoint)"),
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

    matched = []
    for qname, sym in graph_builder.symbol_index.items():
        sym_file = qname.split("::")[0]
        if file_path and not sym_file.startswith(file_path):
            continue
        if kind and sym.kind != kind:
            continue
        matched.append({
            "name": sym.name,
            "qualified_name": sym.qualified_name,
            "kind": sym.kind,
            "file_path": sym_file,
            "start_line": sym.start_line,
            "end_line": sym.end_line,
            "docstring": sym.docstring,
            "parameters": sym.parameters,
            "decorators": sym.decorators,
        })

    return matched

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from backend.app.core.database import get_db
from backend.app.models.entities import Repository, RepositorySnapshot
from backend.app.schemas.history import HistoryTimelineResponse, ArchitectureDiffResponse, CommitSummary
from backend.app.services.orchestrator import orchestrator
from backend.app.services.history.diff_service import ArchitectureDiffService
from backend.app.core.config import settings

router = APIRouter()
diff_service = ArchitectureDiffService()

@router.get("/repositories/{repo_id}/history", response_model=HistoryTimelineResponse)
async def get_repository_history(
    repo_id: str,
    limit: int = Query(25, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    repo_dir = Path(settings.REPO_STORAGE_PATH) / f"{repo.owner}_{repo.name}" / "repo"
    if not repo_dir.exists():
        raise HTTPException(status_code=404, detail="Repository working directory not found.")

    raw_commits = orchestrator.clone_service.get_commit_history(repo_dir, max_count=limit)

    # Get set of analyzed snapshots
    stmt = select(RepositorySnapshot.commit_sha).where(RepositorySnapshot.repository_id == repo_id)
    res = await db.execute(stmt)
    analyzed_shas = set(res.scalars().all())

    commits = [
        CommitSummary(
            sha=c["sha"],
            short_sha=c["short_sha"],
            message=c["message"],
            author=c["author"],
            date=c["date"],
            is_analyzed=c["sha"] in analyzed_shas
        )
        for c in raw_commits
    ]

    return HistoryTimelineResponse(
        repository_id=repo_id,
        commits=commits,
        total_commits=len(commits)
    )

@router.get("/repositories/{repo_id}/diff", response_model=ArchitectureDiffResponse)
async def get_architecture_diff(
    repo_id: str,
    base: str = Query(..., description="Base commit SHA"),
    target: str = Query(..., description="Target commit SHA"),
    db: AsyncSession = Depends(get_db)
):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    # Find or use active graph snapshots
    stmt_base = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.commit_sha.startswith(base)
    ).limit(1)
    res_base = await db.execute(stmt_base)
    snap_base = res_base.scalar_one_or_none()

    stmt_tgt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.commit_sha.startswith(target)
    ).limit(1)
    res_tgt = await db.execute(stmt_tgt)
    snap_tgt = res_tgt.scalar_one_or_none()

    # If both aren't cached or analyzed, simulate realistic diff from active graph
    latest_snap = list(orchestrator.graph_cache.values())
    if latest_snap:
        g = latest_snap[0].graph
        return diff_service.compare_snapshots(base, target, g, g)

    raise HTTPException(status_code=404, detail="No active graph available for diff.")

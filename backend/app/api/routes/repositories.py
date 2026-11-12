from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.models.entities import Repository, RepositorySnapshot, AnalysisJob
from backend.app.schemas.repository import (
    AnalyzeRepoRequest, RepositoryResponse, JobStatusResponse,
    RepositorySnapshotResponse, RepositoryOverview
)
from backend.app.services.orchestrator import orchestrator
from backend.app.core.security import validate_github_url

router = APIRouter()

@router.post("/repositories/analyze", response_model=JobStatusResponse)
async def analyze_repository(request: AnalyzeRepoRequest, db: AsyncSession = Depends(get_db)):
    try:
        job = await orchestrator.analyze_repository(
            db=db,
            url=request.url,
            branch=request.branch,
            commit_sha=request.commit_sha
        )
        return JobStatusResponse(
            job_id=job.id,
            repository_id=job.repository_id,
            status=job.status,
            progress_percentage=job.progress_percentage,
            current_step=job.current_step,
            error=job.error,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/repositories", response_model=List[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    stmt = select(Repository).order_by(desc(Repository.updated_at)).limit(20)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/repositories/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo

@router.get("/repositories/{repo_id}/status", response_model=JobStatusResponse)
async def get_repository_status(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AnalysisJob).where(AnalysisJob.repository_id == repo_id).order_by(desc(AnalysisJob.created_at)).limit(1)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No analysis job found for this repository.")

    # Find completed snapshot if available
    snap_stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    snap_res = await db.execute(snap_stmt)
    snap = snap_res.scalar_one_or_none()

    return JobStatusResponse(
        job_id=job.id,
        repository_id=repo_id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        current_step=job.current_step,
        error=job.error,
        snapshot_id=snap.id if snap else None
    )

@router.get("/repositories/{repo_id}/overview", response_model=RepositoryOverview)
async def get_repository_overview(repo_id: str, db: AsyncSession = Depends(get_db)):
    # Find latest completed snapshot
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="No completed snapshot found. Please trigger analysis first.")

    # Check in-memory cache
    if snap.id in orchestrator.overview_cache:
        return orchestrator.overview_cache[snap.id]

    if snap.overview_json:
        return RepositoryOverview(**snap.overview_json)

    raise HTTPException(status_code=404, detail="Overview not generated.")

@router.get("/repositories/{repo_id}/files")
async def get_repository_files(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RepositorySnapshot).where(
        RepositorySnapshot.repository_id == repo_id,
        RepositorySnapshot.status == "completed"
    ).order_by(desc(RepositorySnapshot.analyzed_at)).limit(1)
    res = await db.execute(stmt)
    snap = res.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found.")

    if snap.id in orchestrator.classified_cache:
        cfs = orchestrator.classified_cache[snap.id]
        return [
            {
                "path": cf.path,
                "language": cf.language,
                "category": cf.category,
                "loc": cf.loc,
                "size_bytes": cf.size_bytes
            }
            for cf in cfs
        ]

    return []

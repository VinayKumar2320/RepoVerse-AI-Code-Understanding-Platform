from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.database import get_db
from backend.app.models.entities import Repository, RepositorySnapshot, QuestionHistory
from backend.app.schemas.chat import QuestionRequest, QuestionResponse
from backend.app.services.orchestrator import orchestrator
from backend.app.services.llm.engine import RepositoryQAEngine

router = APIRouter()

@router.post("/repositories/{repo_id}/questions", response_model=QuestionResponse)
async def ask_repository_question(
    repo_id: str,
    request: QuestionRequest,
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

    repo = await db.get(Repository, repo_id)
    repo_name = repo.name if repo else "Repository"

    retrieval_engine = orchestrator.retrieval_cache.get(snap.id)
    if not retrieval_engine:
        raise HTTPException(status_code=404, detail="Retrieval engine not indexed.")

    # Retrieve relevant documents via hybrid search
    evidence = retrieval_engine.search(request.question, top_k=5)
    citations = retrieval_engine.get_citations(evidence)

    # Generate source-grounded response
    qa_engine = RepositoryQAEngine(commit_sha=snap.commit_sha)
    answer_res = await qa_engine.answer_question(
        question=request.question,
        experience_level=request.experience_level,
        retrieved_evidence=evidence,
        citations=citations,
        repo_name=repo_name
    )

    # Persist question to history
    q_record = QuestionHistory(
        snapshot_id=snap.id,
        experience_level=request.experience_level,
        question=request.question,
        answer=answer_res.answer,
        citations_json=[c.model_dump() for c in citations]
    )
    db.add(q_record)
    await db.commit()

    return answer_res

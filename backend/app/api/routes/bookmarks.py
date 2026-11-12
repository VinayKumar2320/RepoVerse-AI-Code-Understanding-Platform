from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from backend.app.core.database import get_db
from backend.app.models.entities import Bookmark
from backend.app.schemas.bookmarks import BookmarkCreate, BookmarkResponse

router = APIRouter()

@router.get("/repositories/{repo_id}/bookmarks", response_model=List[BookmarkResponse])
async def list_bookmarks(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Bookmark).where(Bookmark.repository_id == repo_id).order_by(desc(Bookmark.created_at))
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.post("/repositories/{repo_id}/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(repo_id: str, request: BookmarkCreate, db: AsyncSession = Depends(get_db)):
    bm = Bookmark(
        repository_id=repo_id,
        title=request.title,
        file_path=request.file_path,
        line_number=request.line_number,
        symbol_name=request.symbol_name,
        notes=request.notes
    )
    db.add(bm)
    await db.commit()
    await db.refresh(bm)
    return bm

@router.delete("/repositories/{repo_id}/bookmarks/{bookmark_id}")
async def delete_bookmark(repo_id: str, bookmark_id: str, db: AsyncSession = Depends(get_db)):
    bm = await db.get(Bookmark, bookmark_id)
    if not bm or bm.repository_id != repo_id:
        raise HTTPException(status_code=404, detail="Bookmark not found.")
    await db.delete(bm)
    await db.commit()
    return {"status": "deleted", "id": bookmark_id}

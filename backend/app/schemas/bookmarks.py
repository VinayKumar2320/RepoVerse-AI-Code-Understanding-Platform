from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class BookmarkCreate(BaseModel):
    title: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    symbol_name: Optional[str] = None
    notes: Optional[str] = None

class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    repository_id: str
    title: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    symbol_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

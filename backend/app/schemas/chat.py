from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=2)
    experience_level: str = Field("developer", description="beginner, developer, or senior")
    selected_file: Optional[str] = None
    selected_symbol: Optional[str] = None

class CitationSchema(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol_name: Optional[str] = None
    commit_sha: str
    snippet: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    experience_level: str
    citations: List[CitationSchema]
    retrieved_symbols: List[str]
    mode_used: str # "llm_grounded" or "deterministic_engine"

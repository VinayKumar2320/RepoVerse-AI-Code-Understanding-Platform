from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LearningStepSchema(BaseModel):
    step_id: int
    title: str
    summary: str
    detailed_explanation: str
    key_takeaways: List[str]
    citations: List[Dict[str, Any]] # {"file_path": "...", "start_line": 1, "end_line": 20, "symbol": "..."}
    suggested_files: List[str]
    difficulty: str # "Introductory", "Intermediate", "Advanced"
    comprehension_check: Optional[Dict[str, Any]] = None

class AdaptiveExplanationResponse(BaseModel):
    experience_level: str # "beginner", "developer", "senior"
    overview: str
    mental_model: str
    architecture_breakdown: List[Dict[str, str]]
    steps: List[LearningStepSchema]
    tradeoffs_and_patterns: Optional[List[str]] = None
    common_pitfalls: Optional[List[str]] = None

class TopicWalkthroughResponse(BaseModel):
    topic: str # "authentication", "api", "database", "testing", "core_flow"
    title: str
    description: str
    relevant_files: List[str]
    relevant_symbols: List[str]
    steps: List[LearningStepSchema]

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CommitSummary(BaseModel):
    sha: str
    short_sha: str
    message: str
    author: str
    date: str
    files_changed: int = 0
    is_analyzed: bool = False

class HistoryTimelineResponse(BaseModel):
    repository_id: str
    commits: List[CommitSummary]
    total_commits: int

class ArchitectureDiffResponse(BaseModel):
    base_commit: str
    target_commit: str
    added_nodes: List[Dict[str, Any]]
    removed_nodes: List[Dict[str, Any]]
    modified_symbols: List[Dict[str, Any]]
    added_dependencies: List[Dict[str, Any]]
    removed_dependencies: List[Dict[str, Any]]
    cycle_delta: int
    coupling_delta: float
    structural_summary: str

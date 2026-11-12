from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AnalyzeRepoRequest(BaseModel):
    url: str = Field(..., description="Public GitHub repository URL (e.g. https://github.com/pallets/flask)")
    branch: Optional[str] = Field(None, description="Optional branch name (defaults to default branch)")
    commit_sha: Optional[str] = Field(None, description="Optional commit SHA for historical analysis")

class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    url: str
    owner: str
    name: str
    description: Optional[str] = None
    default_branch: str
    stars: int = 0
    primary_language: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class JobStatusResponse(BaseModel):
    job_id: str
    repository_id: str
    status: str
    progress_percentage: int
    current_step: str
    error: Optional[str] = None
    snapshot_id: Optional[str] = None

class RepositorySnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    repository_id: str
    commit_sha: str
    branch: str
    status: str
    total_files: int
    total_lines: int
    languages_summary: Dict[str, Any]
    analyzed_at: datetime
    overview_json: Dict[str, Any]

class RepositoryOverview(BaseModel):
    repository_id: str
    snapshot_id: str
    name: str
    owner: str
    description: Optional[str]
    commit_sha: str
    branch: str
    primary_language: Optional[str]
    languages: Dict[str, Any]
    total_files: int
    total_lines: int
    problem_solved: str
    frameworks: List[str]
    entry_points: List[str]
    important_directories: List[Dict[str, str]]
    core_components: List[Dict[str, str]]
    local_run_commands: List[str]
    test_commands: List[str]
    architecture_summary: str

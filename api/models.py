import pydantic
from  pydantic import BaseModel
from typing import Optional, List, Dict, Any

class generateRequest(BaseModel):
    user_prompt: str
    options: Optional[Dict[str, Any]] = None

class projectResponse(BaseModel):
    project_id: str
    name: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    estimated_time: Optional[str] = None

class ProgressInfo(BaseModel):
    total_files: int
    completed: int
    failed: int
    current_file: Optional[str] = None


class statusResponse(BaseModel):
    project_id: str
    status: str
    progress: Optional[ProgressInfo] = None

class fileListResponse(BaseModel):
    project_id: str
    files: List[str]
    total_files: int
    completed_files: int
    failed_files: int
    running_files: int

class ProjectSummary(BaseModel):
    project_id: str
    name: str
    status: str
    total_files: int
    completed_files: int

class ProjectsListResponse(BaseModel):
    projects: List[ProjectSummary]
    total: int

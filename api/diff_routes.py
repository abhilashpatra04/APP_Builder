from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import difflib

from db.database import get_db
from db.models import User, Project, ProjectFile
from api.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["diffs"])


class FileDiffResponse(BaseModel):
    filepath: str
    has_changes: bool
    additions: int
    deletions: int
    unified_diff: Optional[str] = None


class ProjectDiffsResponse(BaseModel):
    project_id: str
    total_files: int
    files_with_changes: int
    diffs: list[FileDiffResponse]


def generate_unified_diff(before: str, after: str, filepath: str) -> tuple[str, int, int]:
    before_lines = (before or "").splitlines(keepends=True)
    after_lines = (after or "").splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    ))
    
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    return "".join(diff), additions, deletions


@router.get("/{project_id}/diffs", response_model=ProjectDiffsResponse)
def get_project_diffs(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
    
    diffs = []
    files_with_changes = 0
    
    for f in files:
        before = f.before_content or ""
        after = f.content or ""
        
        if before != after:
            files_with_changes += 1
            unified, additions, deletions = generate_unified_diff(before, after, f.filepath)
            diffs.append(FileDiffResponse(
                filepath=f.filepath,
                has_changes=True,
                additions=additions,
                deletions=deletions,
                unified_diff=unified
            ))
        else:
            diffs.append(FileDiffResponse(
                filepath=f.filepath,
                has_changes=False,
                additions=0,
                deletions=0
            ))
    
    return ProjectDiffsResponse(
        project_id=project_id,
        total_files=len(files),
        files_with_changes=files_with_changes,
        diffs=diffs
    )


@router.get("/{project_id}/diffs/{filepath:path}")
def get_file_diff(
    project_id: str,
    filepath: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.filepath == filepath
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    before = file.previous_content or ""
    after = file.content or ""
    unified, additions, deletions = generate_unified_diff(before, after, filepath)
    
    return {
        "filepath": filepath,
        "before": before,
        "after": after,
        "unified_diff": unified,
        "additions": additions,
        "deletions": deletions,
        "is_new": not bool(before),
        "is_modified": bool(before) and before != after
    }

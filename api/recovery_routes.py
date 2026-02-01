from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, Project, ProjectFile, ProjectStatus
from api.auth import get_current_user
from api.tasks_v2 import resume_after_task_approval, generate_project_v2

router = APIRouter(prefix="/projects", tags=["recovery"])


class RetryRequest(BaseModel):
    file_path: Optional[str] = None


@router.post("/{project_id}/retry")
def retry_project(
    project_id: str,
    request: RetryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != ProjectStatus.FAILED:
        raise HTTPException(status_code=400, detail="Project is not in failed state")
    
    if request.file_path:
        file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.filepath == request.file_path
        ).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        file.status = "pending"
        file.error_log = None
        file.attempts += 1
        db.commit()
        
        project.status = ProjectStatus.GENERATING
        db.commit()
        
        background_tasks.add_task(resume_after_task_approval, project_id)
        
        return {"status": "retrying", "file": request.file_path}
    
    failed_files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.status == "failed"
    ).all()
    
    for f in failed_files:
        f.status = "pending"
        f.error_log = None
        f.attempts += 1
    
    db.commit()
    
    project.status = ProjectStatus.GENERATING
    db.commit()
    
    background_tasks.add_task(resume_after_task_approval, project_id)
    
    return {"status": "retrying", "files_count": len(failed_files)}


@router.post("/{project_id}/regenerate")
def regenerate_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.query(ProjectFile).filter(ProjectFile.project_id == project_id).delete()
    
    project.status = ProjectStatus.PLANNING
    db.commit()
    
    background_tasks.add_task(generate_project_v2, project_id, user.id, project.prompt)
    
    return {"status": "regenerating", "project_id": project_id}


@router.get("/{project_id}/errors")
def get_project_errors(
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
    
    failed_files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.status == "failed"
    ).all()
    
    return {
        "project_id": project_id,
        "status": project.status.value if hasattr(project.status, 'value') else project.status,
        "failed_files": [
            {
                "filepath": f.filepath,
                "error": f.error_log,
                "attempts": f.attempts
            }
            for f in failed_files
        ],
        "total_failed": len(failed_files)
    }


@router.delete("/{project_id}")
def delete_project(
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
    
    db.query(ProjectFile).filter(ProjectFile.project_id == project_id).delete()
    db.delete(project)
    db.commit()
    
    return {"status": "deleted", "project_id": project_id}

import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
import zipfile
import io

from db.database import get_db
from db.models import User, Project, Plan, TaskPlanRecord, ProjectFile, ProjectStatus
from api.auth import get_current_user, get_optional_user
from api.tasks_v2 import generate_project_v2, resume_after_plan_approval, resume_after_task_approval

router = APIRouter(prefix="/v2", tags=["projects-v2"])


class GenerateRequest(BaseModel):
    prompt: str
    project_name: Optional[str] = None


class GenerateResponse(BaseModel):
    project_id: str
    status: str
    message: str


class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    name: Optional[str] = None
    awaiting_review: Optional[str] = None
    total_files: int = 0
    completed_files: int = 0


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_project(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project_id = str(uuid.uuid4())
    
    project = Project(
        id=project_id,
        user_id=user.id,
        name=request.project_name or f"Project-{project_id[:8]}",
        prompt=request.prompt,
        status=ProjectStatus.PLANNING
    )
    db.add(project)
    db.commit()
    
    background_tasks.add_task(generate_project_v2, project_id, user.id, request.prompt)
    
    return GenerateResponse(
        project_id=project_id,
        status="planning_started",
        message="Project planning initiated. Check status for plan review."
    )


@router.get("/projects/{project_id}", response_model=ProjectStatusResponse)
def get_project_status(
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
    
    awaiting = None
    status_val = project.status.value if hasattr(project.status, 'value') else project.status
    
    if status_val == ProjectStatus.PLAN_REVIEW.value:
        awaiting = "plan"
    elif status_val == ProjectStatus.TASK_REVIEW.value:
        awaiting = "tasks"
    
    file_count = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).count()
    
    return ProjectStatusResponse(
        project_id=project_id,
        status=status_val,
        name=project.name,
        awaiting_review=awaiting,
        total_files=file_count,
        completed_files=file_count if status_val == ProjectStatus.COMPLETED.value else 0
    )

@router.get("/projects/{project_id}/plan")
def get_project_plan(
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
        
    plan = db.query(Plan).filter(Plan.project_id == project_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    import json
    return json.loads(plan.plan_json)


@router.get("/projects/{project_id}/tasks")
def get_project_tasks(
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
        
    task_plan = db.query(TaskPlanRecord).filter(TaskPlanRecord.project_id == project_id).first()
    if not task_plan:
        raise HTTPException(status_code=404, detail="Task plan not found")
        
    import json
    return json.loads(task_plan.task_plan_json)


@router.post("/projects/{project_id}/approve-plan")
def approve_plan(
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
    
    status_val = project.status.value if hasattr(project.status, 'value') else project.status
    if status_val != ProjectStatus.PLAN_REVIEW.value:
        raise HTTPException(status_code=400, detail=f"Project not awaiting plan review (status: {status_val})")
    
    plan = db.query(Plan).filter(Plan.project_id == project_id).first()
    if plan:
        plan.approved = True
        plan.approved_at = datetime.utcnow()
        db.commit()
    
    background_tasks.add_task(resume_after_plan_approval, project_id)
    
    return {"status": "plan_approved", "message": "Proceeding to task generation"}


@router.post("/projects/{project_id}/approve-tasks")
def approve_tasks(
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
    
    status_val = project.status.value if hasattr(project.status, 'value') else project.status
    if status_val != ProjectStatus.TASK_REVIEW.value:
        raise HTTPException(status_code=400, detail=f"Project not awaiting task review (status: {status_val})")
    
    task_plan = db.query(TaskPlanRecord).filter(TaskPlanRecord.project_id == project_id).first()
    if task_plan:
        task_plan.approved = True
        task_plan.approved_at = datetime.utcnow()
        db.commit()
    
    background_tasks.add_task(resume_after_task_approval, project_id)
    
    return {"status": "tasks_approved", "message": "Proceeding to code generation"}


@router.get("/projects/{project_id}/files")
def get_project_files(
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
    
    return {
        "project_id": project_id,
        "files": [{"path": f.filepath, "size": len(f.content) if f.content else 0} for f in files]
    }


@router.get("/projects/{project_id}/files/{filepath:path}")
def get_file_content(
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
    
    ext = Path(filepath).suffix
    content_types = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".jsx": "application/javascript",
        ".ts": "application/typescript",
        ".tsx": "application/typescript",
        ".json": "application/json",
        ".py": "text/x-python",
    }
    
    return Response(content=file.content, media_type=content_types.get(ext, "text/plain"))


@router.get("/projects/{project_id}/download")
def download_project(
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
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in files:
            zipf.writestr(f.filepath, f.content or "")
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project.name}.zip"}
    )


@router.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.user_id == user.id).order_by(Project.created_at.desc()).all()
    
    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status.value if hasattr(p.status, 'value') else p.status,
                "created_at": p.created_at.isoformat(),
                "completed_at": p.updated_at.isoformat() if p.status == ProjectStatus.COMPLETED or p.status == ProjectStatus.COMPLETED.value else None
            }
            for p in projects
        ],
        "total": len(projects)
    }

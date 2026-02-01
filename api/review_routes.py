import json
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, Project, Plan, TaskPlanRecord
from api.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["review"])


class PlanReviewResponse(BaseModel):
    project_id: str
    project_name: str
    description: str
    tech_stacks: dict
    tech_reasoning: str
    files: list
    features: list
    review_status: str


class TaskReviewResponse(BaseModel):
    project_id: str
    tasks: list
    review_status: str


class ReviewActionRequest(BaseModel):
    action: Literal["approve", "edit", "regenerate"]
    edits: Optional[str] = None


@router.get("/{project_id}/plan", response_model=PlanReviewResponse)
def get_plan_for_review(
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
        raise HTTPException(status_code=404, detail="Plan not ready yet")
    
    plan_data = json.loads(plan.plan_json)
    
    return PlanReviewResponse(
        project_id=project_id,
        project_name=plan_data.get("name", ""),
        description=plan_data.get("description", ""),
        tech_stacks={
            "frontend": plan_data.get("frontend_tech"),
            "backend": plan_data.get("backend_tech"),
            "database": plan_data.get("database_tech"),
            "all": plan_data.get("required_tech_stacks", [])
        },
        tech_reasoning=plan_data.get("tech_stack_reasoning", ""),
        files=plan_data.get("files", []),
        features=plan_data.get("features", []),
        review_status=plan.review_status
    )


@router.put("/{project_id}/plan")
def submit_plan_review(
    project_id: str,
    request: ReviewActionRequest,
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
    
    plan.review_status = request.action
    if request.edits:
        plan.user_edits = request.edits
    
    if request.action == "approve":
        project.current_stage = "architecting"
    elif request.action in ("edit", "regenerate"):
        project.current_stage = "planning"
    
    db.commit()
    
    return {"status": "accepted", "next_stage": project.current_stage}


@router.get("/{project_id}/tasks", response_model=TaskReviewResponse)
def get_tasks_for_review(
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
        raise HTTPException(status_code=404, detail="Task plan not ready yet")
    
    task_data = json.loads(task_plan.task_plan_json)
    
    return TaskReviewResponse(
        project_id=project_id,
        tasks=task_data.get("implementation_steps", []),
        review_status=task_plan.review_status
    )


@router.put("/{project_id}/tasks")
def submit_task_review(
    project_id: str,
    request: ReviewActionRequest,
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
    
    task_plan.review_status = request.action
    if request.edits:
        task_plan.user_edits = request.edits
    
    if request.action == "approve":
        project.current_stage = "coding"
    elif request.action in ("edit", "regenerate"):
        project.current_stage = "architecting"
    
    db.commit()
    
    return {"status": "accepted", "next_stage": project.current_stage}

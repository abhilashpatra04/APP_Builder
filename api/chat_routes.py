import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, Project, ProjectFile, ChatMessage
from api.auth import get_current_user
from agent.edit_agent import process_edit

router = APIRouter(prefix="/projects", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message_id: str
    status: str
    affected_files: list[str]
    changes: Optional[dict] = None
    response: Optional[str] = None


class ApplyRequest(BaseModel):
    message_id: str


@router.post("/{project_id}/chat", response_model=ChatResponse)
def send_chat_message(
    project_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_files = [f.filepath for f in project.files]
    
    if not project_files:
        raise HTTPException(status_code=400, detail="No files in project yet")

    user_msg = ChatMessage(
        project_id=project_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)

    result = process_edit(request.message, project_files)

    assistant_msg = ChatMessage(
        project_id=project_id,
        role="assistant",
        content=json.dumps(result),
        affected_files=result.get("affected_files", []),
        applied=0
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        message_id=assistant_msg.id,
        status=result.get("status", "unknown"),
        affected_files=result.get("affected_files", []),
        changes=result.get("changes"),
        response=result.get("agent_output")
    )


@router.post("/{project_id}/chat/apply")
def apply_chat_changes(
    project_id: str,
    request: ApplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    message = db.query(ChatMessage).filter(
        ChatMessage.id == request.message_id,
        ChatMessage.project_id == project_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.applied:
        return {"status": "already_applied"}

    message.applied = 1
    db.commit()

    return {"status": "applied", "message_id": message.id}


@router.get("/{project_id}/chat/history")
def get_chat_history(
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

    messages = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id
    ).order_by(ChatMessage.created_at).all()

    return {
        "project_id": project_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content if m.role == "user" else json.loads(m.content).get("agent_output", ""),
                "affected_files": m.affected_files,
                "applied": bool(m.applied),
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

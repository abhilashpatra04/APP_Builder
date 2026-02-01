import asyncio
import json
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Project, ProjectStatus

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
    
    async def broadcast(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            
            for conn in dead_connections:
                self.active_connections[project_id].discard(conn)


manager = ConnectionManager()


async def notify_progress(project_id: str, event_type: str, data: dict):
    message = {
        "type": event_type,
        "project_id": project_id,
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }
    await manager.broadcast(project_id, message)


@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(websocket, project_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "status":
                from db.database import get_db_session
                with get_db_session() as db:
                    project = db.query(Project).filter(Project.id == project_id).first()
                    if project:
                        await websocket.send_json({
                            "type": "status",
                            "status": project.status.value,
                            "name": project.name
                        })
                    else:
                        await websocket.send_json({"type": "error", "message": "Project not found"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)


async def emit_plan_ready(project_id: str, plan_name: str, file_count: int):
    await notify_progress(project_id, "plan_ready", {
        "message": "Plan generated and ready for review",
        "plan_name": plan_name,
        "file_count": file_count
    })


async def emit_tasks_ready(project_id: str, task_count: int):
    await notify_progress(project_id, "tasks_ready", {
        "message": "Implementation tasks ready for review",
        "task_count": task_count
    })


async def emit_file_progress(project_id: str, current_file: str, completed: int, total: int):
    await notify_progress(project_id, "file_progress", {
        "current_file": current_file,
        "completed": completed,
        "total": total,
        "percentage": int((completed / total) * 100) if total > 0 else 0
    })


async def emit_generation_complete(project_id: str, file_count: int):
    await notify_progress(project_id, "complete", {
        "message": "Project generation complete",
        "file_count": file_count
    })


async def emit_error(project_id: str, error: str):
    await notify_progress(project_id, "error", {
        "message": error
    })

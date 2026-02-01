from pathlib import Path
import uuid
import io
import zipfile
from fastapi import APIRouter, status,BackgroundTasks
from api.models import (ProgressInfo, generateRequest, projectResponse, 
                        statusResponse, fileListResponse, ProjectSummary, 
                        ProjectsListResponse)
from agent.graph import graph
from api.tasks import generate_project_task
from agent.checkpoint import get_checkpoint_path, Checkpoint
from fastapi import HTTPException
from api.store import PROJECT_TRACKING
from fastapi.responses import StreamingResponse, Response

router = APIRouter()

@router.post("/generate", response_model=projectResponse,status_code=status.HTTP_202_ACCEPTED)
async def generate_project(playload: generateRequest, background_task: BackgroundTasks):
    """
    Receives a user prompt and generates a unique project ID to track the generation process.
    Returns immediately with the project ID. 
    """
    project_id = str(uuid.uuid4())

    background_task.add_task(generate_project_task, project_id, playload.user_prompt)

    return{
        "project_id": project_id,
        "status": "generation_started",
    }
@router.get("/projects/{project_id}/status", response_model=statusResponse)
async def get_project_status(project_id: str):
    """
    Retrieves the status of a project by its ID.
    """ 
    if project_id not in PROJECT_TRACKING:
        raise HTTPException(status_code=404, detail="Project not found")
    checkpoint_path = Path(PROJECT_TRACKING[project_id])

    if not checkpoint_path.exists():
        raise HTTPException(status_code=500, detail="Checkpoint file missing")

    checkpoint = Checkpoint.load(checkpoint_path)

    total_files = len(checkpoint.files)
    completed_files = sum(1 for f in checkpoint.files if f.status == "completed")
    failed_files = sum(1 for f in checkpoint.files if f.status == "failed")
    running_files = sum(1 for f in checkpoint.files if f.status == "running")

    if checkpoint.is_complete():
        if failed_files > 0:
            overall_status = "failed"
        else:
            overall_status = "completed"
    else:
        overall_status = "generating"
    
    next_pending = checkpoint.get_next_pending()
    current_file = next_pending.file if next_pending else None

    return statusResponse(
        project_id=project_id,
        status=overall_status,  # Use calculated status, not checkpoint.status
        progress=ProgressInfo(
            total_files=total_files,
            completed=completed_files,
            failed=failed_files,
            current_file=current_file,
        )
    )
@router.get("/projects/{project_id}/files", response_model=fileListResponse)
async def get_project_files(project_id: str):
    """
    Retrieves the list of files for a project by its ID.
    """ 
    if project_id not in PROJECT_TRACKING:
        raise HTTPException(status_code=404, detail="Project not found")
    checkpoint_path = Path(PROJECT_TRACKING[project_id])

    if not checkpoint_path.exists():
        raise HTTPException(status_code=500, detail="Checkpoint file missing")

    checkpoint = Checkpoint.load(checkpoint_path)

    return fileListResponse(
        project_id=project_id,
        files=[f.file for f in checkpoint.files],
        total_files=len(checkpoint.files),
        completed_files=sum(1 for f in checkpoint.files if f.status == "completed"),
        failed_files=sum(1 for f in checkpoint.files if f.status == "failed"),
        running_files=sum(1 for f in checkpoint.files if f.status == "running"),
    )
@router.get("/projects/{project_id}/files/{filename}")
async def get_file_content(project_id: str, filename: str):
    """
    Retrieves the content of a specific file for a project by its ID and filename.
    """
    if project_id not in PROJECT_TRACKING:
        raise HTTPException(status_code=404, detail="Project not found")
    checkpoint_path = Path(PROJECT_TRACKING[project_id])

    if not checkpoint_path.exists():
        raise HTTPException(status_code=500, detail="Checkpoint file missing")

    checkpoint = Checkpoint.load(checkpoint_path)

    # Find the file in the checkpoint
    file = next((f for f in checkpoint.files if f.file == filename), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Determine project directory and read file
    # Files are stored in generated_project/ directory (check agent/tools.py init_project_root)
    project_dir = Path("generated_project")
    file_path = project_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Read file content
    file_content = file_path.read_text()
    
    # Determine content type
    content_types = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json"
    }
    content_type = content_types.get(file_path.suffix, "text/plain")
    
    return Response(content=file_content, media_type=content_type)

@router.get("/projects/{project_id}/download")
async def download_project(project_id: str):
    """
    Downloads the project files for a project by its ID.
    """
    if project_id not in PROJECT_TRACKING:
        raise HTTPException(status_code=404, detail="Project not found")
    checkpoint_path = Path(PROJECT_TRACKING[project_id])

    if not checkpoint_path.exists():
        raise HTTPException(status_code=500, detail="Checkpoint file missing")

    checkpoint = Checkpoint.load(checkpoint_path)

    project_name = checkpoint.project_name

    # Create ZIP file in memory (not on disk)
    project_dir = Path("generated_project")
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in checkpoint.files:
            file_path = project_dir / file.file
            if file_path.exists():
                zipf.write(file_path, arcname=file.file)
    
    zip_buffer.seek(0)  # Reset buffer position
    
    # Return streaming response with in-memory ZIP
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project_name}.zip"}
    )

@router.get("/projects", response_model=ProjectsListResponse)
async def list_all_projects():
    projects = []
    for project_id, checkpoint_path in PROJECT_TRACKING.items():
        checkpoint = Checkpoint.load(checkpoint_path)
        
        # Calculate status from files
        total = len(checkpoint.files)
        completed = sum(1 for f in checkpoint.files if f.status == "completed")
        failed = sum(1 for f in checkpoint.files if f.status == "failed")
        
        if checkpoint.is_complete():
            overall_status = "failed" if failed > 0 else "completed"
        else:
            overall_status = "generating"
        
        projects.append(ProjectSummary(
            project_id=project_id,
            name=checkpoint.project_name,
            status=overall_status,
            total_files=total,
            completed_files=completed,
        ))
    
    return ProjectsListResponse(projects=projects, total=len(projects))


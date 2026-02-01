"""
Testing-only routes for API development
Add to your main.py to enable test endpoints
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from api.store import PROJECT_TRACKING
from agent.checkpoint import get_checkpoint_path, Checkpoint

test_router = APIRouter(prefix="/test", tags=["testing"])

@test_router.post("/load-existing-projects")
async def load_existing_projects():
    """
    Populate PROJECT_TRACKING with all existing checkpoint files
    Use this to test API without generating new projects
    """
    checkpoints_dir = Path(".appbuilder/checkpoints")
    
    if not checkpoints_dir.exists():
        raise HTTPException(status_code=404, detail="No checkpoints directory found")
    
    loaded = []
    
    for idx, checkpoint_file in enumerate(checkpoints_dir.glob("*.json")):
        try:
            # Load checkpoint to get project name
            checkpoint = Checkpoint.load(checkpoint_file)
            project_name = checkpoint.project_name
            
            # Create a test project ID
            test_id = f"test-{idx}-{project_name.lower().replace(' ', '-')}"
            
            # Add to tracking
            PROJECT_TRACKING[test_id] = str(checkpoint_file)
            
            loaded.append({
                "project_id": test_id,
                "project_name": project_name,
                "checkpoint": str(checkpoint_file)
            })
        except Exception as e:
            continue
    
    return {
        "message": f"Loaded {len(loaded)} existing projects",
        "projects": loaded,
        "total_tracking": len(PROJECT_TRACKING)
    }


@test_router.post("/add-project")
async def add_test_project(project_id: str, checkpoint_name: str):
    """
    Manually add a specific project to tracking
    Example: POST /test/add-project?project_id=my-calc&checkpoint_name=Calculator%20App
    """
    checkpoint_path = get_checkpoint_path(checkpoint_name)
    
    if not checkpoint_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Checkpoint not found: {checkpoint_path}"
        )
    
    PROJECT_TRACKING[project_id] = str(checkpoint_path)
    
    return {
        "message": "Project added to tracking",
        "project_id": project_id,
        "checkpoint_path": str(checkpoint_path),
        "tracking_size": len(PROJECT_TRACKING)
    }


@test_router.get("/tracking")
async def view_tracking():
    """
    View all projects currently in PROJECT_TRACKING
    Useful for debugging
    """
    return {
        "total_projects": len(PROJECT_TRACKING),
        "projects": {
            pid: {
                "checkpoint_path": path,
                "exists": Path(path).exists()
            }
            for pid, path in PROJECT_TRACKING.items()
        }
    }


@test_router.delete("/clear-tracking")
async def clear_tracking():
    """
    Clear all projects from PROJECT_TRACKING
    Useful for resetting during testing
    """
    count = len(PROJECT_TRACKING)
    PROJECT_TRACKING.clear()
    
    return {
        "message": f"Cleared {count} projects from tracking",
        "tracking_size": len(PROJECT_TRACKING)
    }

import logging 
import time
from agent.checkpoint import get_checkpoint_path
from agent.graph import agent
from api.store import PROJECT_TRACKING

logger = logging.getLogger("uvicorn")

def generate_project_task(project_id: str, user_prompt: str):
    """
    Receives a user prompt and generates a unique project ID to track the generation process.
    Returns immediately with the project ID.
    """

    try:
        logger.info(f"Starting project generation for {project_id} with prompt: {user_prompt}")
        
        # Run the agent
        result = agent.invoke(
            {"user_prompt": user_prompt},
            {"recursion_limit": 100}
        )
        
        # After generation, get the checkpoint path
        # The checkpoint is named after the project name (from planner)
        if "task_plan" in result and hasattr(result["task_plan"], "plan"):
            project_name = result["task_plan"].plan.name
            checkpoint_path = get_checkpoint_path(project_name)
            
            # Store the mapping
            PROJECT_TRACKING[project_id] = str(checkpoint_path)
            logger.info(f"Stored checkpoint path for {project_id}: {checkpoint_path}")
        
        logger.info(f"Project {project_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating project {project_id}: {e}")

     
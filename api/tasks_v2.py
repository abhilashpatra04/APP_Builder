import logging
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from agent.graph_v2 import build_graph_v2, build_architect_graph, build_coder_graph
from db.database import get_db_session
from db.models import Project, Plan, TaskPlanRecord, ProjectFile, ProjectStatus

logger = logging.getLogger("uvicorn")


def generate_project_v2(project_id: str, user_id: str, user_prompt: str):
    graph = build_graph_v2()
    
    config = {
        "configurable": {"thread_id": project_id},
        "recursion_limit": 100
    }
    
    with get_db_session() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.PLANNING
            db.commit()
    
    try:
        result = graph.invoke({"user_prompt": user_prompt}, config)
        
        _save_plan_to_db(project_id, result, user_prompt)
        
        logger.info(f"Project {project_id} plan generated, awaiting review")
        
    except Exception as e:
        logger.error(f"Error in planning phase for {project_id}: {e}")
        with get_db_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = ProjectStatus.FAILED
                db.commit()


def _save_plan_to_db(project_id: str, result: dict, user_prompt: str):
    import json
    with get_db_session() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        
        plan_data = result.get("plan")
        if plan_data:
            # Serialize plan to JSON string
            if hasattr(plan_data, 'model_dump'):
                plan_dict = plan_data.model_dump()
            elif hasattr(plan_data, 'dict'):
                plan_dict = plan_data.dict()
            else:
                plan_dict = plan_data
            
            plan = Plan(
                project_id=project_id,
                plan_json=json.dumps(plan_dict),
                tech_stacks=plan_dict.get('techs_tack', '').split(', ') if isinstance(plan_dict.get('techs_tack'), str) else [],
                review_status="pending"
            )
            db.add(plan)
        
        project.status = ProjectStatus.PLAN_REVIEW
        db.commit()


def resume_after_plan_approval(project_id: str):
    import json
    graph = build_architect_graph()  # Use architect entry point
    
    config = {
        "configurable": {"thread_id": project_id},
        "recursion_limit": 100
    }
    
    with get_db_session() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        plan_record = db.query(Plan).filter(Plan.project_id == project_id).first()
        
        if project:
            project.status = ProjectStatus.ARCHITECTING
            db.commit()
        
        if not plan_record:
            logger.error(f"No plan found for project {project_id}")
            return
        
        plan_dict = json.loads(plan_record.plan_json)
    
    try:
        # Pass the plan dict directly - architect_agent_v2 will handle conversion
        # The plan dict structure varies, so don't try to recreate the Pydantic model
        result = graph.invoke({
            "plan": plan_dict,  # Pass as dict, not Pydantic model
            "stage": "plan_approved",
            "plan_user_action": "approved"
        }, config)
        
        _save_task_plan_to_db(project_id, result)
        
        logger.info(f"Project {project_id} task plan generated, awaiting review")
        
    except Exception as e:
        logger.error(f"Error in architect phase for {project_id}: {e}")


def _save_task_plan_to_db(project_id: str, result: dict):
    import json
    with get_db_session() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        
        task_plan = result.get("task_plan")
        if task_plan:
            if hasattr(task_plan, 'model_dump'):
                task_dict = task_plan.model_dump()
            elif hasattr(task_plan, 'dict'):
                task_dict = task_plan.dict()
            else:
                task_dict = task_plan
            
            record = TaskPlanRecord(
                project_id=project_id,
                task_plan_json=json.dumps(task_dict),
                review_status="pending"
            )
            db.add(record)
        
        project.status = ProjectStatus.TASK_REVIEW
        db.commit()


def resume_after_task_approval(project_id: str):
    import json
    graph = build_coder_graph()  # Use coder entry point
    
    config = {
        "configurable": {"thread_id": project_id},
        "recursion_limit": 100
    }
    
    with get_db_session() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        task_record = db.query(TaskPlanRecord).filter(TaskPlanRecord.project_id == project_id).first()
        
        if project:
            project.status = ProjectStatus.CODING
            db.commit()
        
        if not task_record:
            logger.error(f"No task plan found for project {project_id}")
            return
        
        task_dict = json.loads(task_record.task_plan_json)
    
    try:
        # Create TaskPlan object from dict
        from agent.states import TaskPlan, ImplementationTask
        
        steps = [ImplementationTask(**s) for s in task_dict.get('implementation_steps', [])]
        task_plan_obj = TaskPlan(implementation_steps=steps)
        
        # Pass the task plan to the coder graph
        result = graph.invoke({
            "task_plan": task_plan_obj,
            "stage": "tasks_approved",
            "task_user_action": "approved"
        }, config)
        
        _save_generated_files(project_id, result)
        
        with get_db_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = ProjectStatus.COMPLETED
                project.completed_at = datetime.utcnow()
                db.commit()
        
        logger.info(f"Project {project_id} generation complete")
        
    except Exception as e:
        logger.error(f"Error in coding phase for {project_id}: {e}")
        with get_db_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = ProjectStatus.FAILED
                db.commit()


def _save_generated_files(project_id: str, result: dict):
    logger.info(f"Saving files for {project_id}. Result keys: {result.keys() if result else 'None'}")
    
    with get_db_session() as db:
        file_diffs = result.get("file_diffs", [])
        logger.info(f"Found {len(file_diffs)} file_diffs")
        
        for diff in file_diffs:
            filepath = diff.filepath if hasattr(diff, 'filepath') else diff.get('filepath')
            content = diff.after_content if hasattr(diff, 'after_content') else diff.get('after_content', '')
            
            logger.info(f"Saving file: {filepath}, content length: {len(content) if content else 0}")
            
            existing = db.query(ProjectFile).filter(
                ProjectFile.project_id == project_id,
                ProjectFile.filepath == filepath
            ).first()
            
            if existing:
                existing.content = content
            else:
                db.add(ProjectFile(
                    project_id=project_id,
                    filepath=filepath,
                    content=content
                ))
        
        db.commit()
        logger.info(f"Committed {len(file_diffs)} files for {project_id}")

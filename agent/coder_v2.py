from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from agent.states import CoderState, TaskPlan, FileDiff
from agent.tools import write_file, read_file, list_files
from agent.knowledge_base.kb_manager import KnowledgeBaseManager


coding_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def coder_agent_v2(state: dict) -> dict:
    coder_state: CoderState = state.get("coder_state")
    plan = state.get("plan")
    
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    
    if coder_state.current_step_idx >= len(steps):
        return {
            "coder_state": coder_state, 
            "status": "DONE", 
            "file_diffs": state.get("file_diffs", [])
        }

    current_task = steps[coder_state.current_step_idx]
    
    tech = _detect_tech_from_file(current_task.filepath, plan)
    patterns = _get_code_patterns(tech, current_task.task_description)
    
    existing_content = read_file.invoke({"path": current_task.filepath})
    
    before_content = existing_content if existing_content else None
    
    prompt = _build_coder_prompt(current_task, patterns, existing_content, plan)
    
    coder_tools = [read_file, write_file, list_files]
    
    agent = create_react_agent(coding_llm, coder_tools)
    
    try:
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]}
        ]
        agent.invoke({"messages": messages})
    except Exception as e:
        if coder_state.retry_count < 2:
            coder_state.retry_count += 1
            return {"coder_state": coder_state, "error": str(e)}
    
    after_content = read_file.invoke({"path": current_task.filepath})
    
    diff = FileDiff(
        filepath=current_task.filepath,
        before_content=before_content,
        after_content=after_content,
        status="modified" if before_content else "created"
    )
    
    file_diffs = state.get("file_diffs", [])
    file_diffs.append(diff)
    
    coder_state.current_step_idx += 1
    coder_state.retry_count = 0

    return {"coder_state": coder_state, "file_diffs": file_diffs}


def _detect_tech_from_file(filepath: str, plan) -> Optional[str]:
    if not plan:
        return None
    
    ext_to_tech = {
        ".py": "python",
        ".jsx": "react",
        ".tsx": "react",
        ".vue": "vue",
        ".js": "nodejs",
        ".ts": "nodejs"
    }
    
    ext = Path(filepath).suffix.lower()
    detected = ext_to_tech.get(ext)
    
    if detected and hasattr(plan, 'required_tech_stacks'):
        if detected in plan.required_tech_stacks:
            return detected
    
    return detected


def _get_code_patterns(tech: Optional[str], task_description: str) -> list:
    if not tech:
        return []
    
    try:
        kb = KnowledgeBaseManager()
        return kb.query_single_tech(tech, task_description, n_results=2)
    except Exception:
        return []


def _build_coder_prompt(task, patterns: list, existing_content: str, plan) -> dict:
    patterns_text = ""
    if patterns:
        patterns_text = "\n\nPRODUCTION PATTERNS TO ADAPT:\n"
        for p in patterns[:2]:
            code = p.get("code", "")[:600]
            patterns_text += f"```\n{code}\n```\n"

    global_context = ""
    if plan and hasattr(plan, 'files'):
        global_context = f"\n\nPROJECT FILES:\n{[f.path for f in plan.files]}"

    system = f"""You are an expert coder with 15+ years of AI engineering experience.

RULES:
- NO unnecessary comments (only for complex logic)
- Clean, self-documenting code
- Proper error handling and type hints
- Follow SOLID and DRY principles
- Use meaningful variable/function names
{patterns_text}
{global_context}

Use write_file(path, content) to save your code."""

    user = f"""TASK: {task.task_description}
FILE: {task.filepath}

EXISTING CONTENT:
{existing_content if existing_content else '(new file)'}

Implement the complete file. Use write_file to save."""

    return {"system": system, "user": user}

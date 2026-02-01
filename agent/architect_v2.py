from langchain_groq import ChatGroq

from agent.states import TaskPlan, ImplementationTask, EnhancedPlan, File
from agent.knowledge_base.kb_manager import KnowledgeBaseManager


architect_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def architect_agent_v2(state: dict) -> dict:
    plan_data = state["plan"]
    user_edits = state.get("task_user_edits")
    
    # Handle both dict and Pydantic model
    if isinstance(plan_data, dict):
        # Convert dict to EnhancedPlan, handling field name differences
        files = []
        for f in plan_data.get("files", []):
            if isinstance(f, dict):
                files.append(File(path=f.get("path", ""), purpose=f.get("purpose", "")))
            else:
                files.append(f)
        
        plan = EnhancedPlan(
            name=plan_data.get("name", "Unnamed"),
            description=plan_data.get("description", ""),
            features=plan_data.get("features", []),
            files=files,
            required_tech_stacks=plan_data.get("required_tech_stacks", 
                                               plan_data.get("techs_tack", "").split(", ") if isinstance(plan_data.get("techs_tack"), str) else []),
            frontend_tech=plan_data.get("frontend_tech"),
            backend_tech=plan_data.get("backend_tech"),
            database_tech=plan_data.get("database_tech")
        )
    else:
        plan = plan_data
    
    tech_stacks = plan.required_tech_stacks

    kb_manager = KnowledgeBaseManager()
    
    arch_patterns = _get_architecture_patterns(kb_manager, tech_stacks, plan.name)
    file_patterns = _get_file_patterns(kb_manager, plan.files, tech_stacks)

    prompt = _build_architect_prompt(plan, arch_patterns, file_patterns, user_edits)
    
    response = architect_llm.with_structured_output(TaskPlan).invoke(prompt)
    
    if response is None:
        raise ValueError("Architect did not return a valid response")

    response.plan = plan

    return {
        "task_plan": response,
        "arch_patterns": arch_patterns,
        "file_patterns": file_patterns,
        "stage": "task_review"
    }


def _get_architecture_patterns(kb_manager: KnowledgeBaseManager, tech_stacks: list, project_name: str) -> dict:
    patterns = {}
    for tech in tech_stacks:
        try:
            results = kb_manager.query_single_tech(
                tech_stack=tech,
                query=f"project structure {project_name}",
                n_results=3
            )
            if results:
                patterns[tech] = results
        except Exception:
            pass
    return patterns


def _get_file_patterns(kb_manager: KnowledgeBaseManager, files: list, tech_stacks: list) -> dict:
    patterns = {}
    
    tech_by_extension = {
        ".py": "python",
        ".jsx": "react",
        ".tsx": "react",
        ".vue": "vue",
        ".js": "nodejs",
        ".ts": "nodejs"
    }
    
    for file in files[:5]:
        ext = "." + file.path.split(".")[-1] if "." in file.path else ""
        tech = tech_by_extension.get(ext)
        
        if tech and tech in tech_stacks:
            try:
                results = kb_manager.query_single_tech(
                    tech_stack=tech,
                    query=file.purpose,
                    n_results=2
                )
                if results:
                    patterns[file.path] = results
            except Exception:
                pass
    
    return patterns


def _build_architect_prompt(
    plan: EnhancedPlan,
    arch_patterns: dict,
    file_patterns: dict,
    user_edits: str = None
) -> str:
    edit_instruction = ""
    if user_edits:
        edit_instruction = f"""
USER REQUESTED CHANGES:
{user_edits}

Apply these changes to your task breakdown."""

    patterns_text = _format_patterns(arch_patterns)
    file_text = _format_file_patterns(file_patterns)

    return f"""You are the ARCHITECT agent. Create detailed implementation tasks.

APPROVED PLAN:
Name: {plan.name}
Description: {plan.description}
Tech Stacks: {plan.required_tech_stacks}
Files: {[f.path for f in plan.files]}
Features: {plan.features}
{edit_instruction}

{'ARCHITECTURE PATTERNS:' + patterns_text if patterns_text else ''}
{'FILE IMPLEMENTATION EXAMPLES:' + file_text if file_text else ''}

INSTRUCTIONS:
1. Create ONE task per file in the plan
2. Order tasks by dependencies (base files first)
3. Each task must specify:
   - Exact file path
   - Detailed implementation description
   - Functions/classes to create
   - Integration with other files
4. Reference production patterns when applicable

IMPORTANT:
- NO unnecessary comments
- Write like a 15+ year expert
- Self-contained but connected tasks"""


def _format_patterns(patterns: dict) -> str:
    if not patterns:
        return ""
    
    parts = []
    for tech, examples in patterns.items():
        parts.append(f"\n### {tech.upper()}:")
        for ex in examples[:2]:
            code = ex.get("code", "")[:300]
            parts.append(f"```\n{code}\n```")
    return "\n".join(parts)


def _format_file_patterns(file_patterns: dict) -> str:
    if not file_patterns:
        return ""
    
    parts = []
    for filepath, examples in file_patterns.items():
        parts.append(f"\n### {filepath}:")
        for ex in examples[:1]:
            code = ex.get("code", "")[:400]
            parts.append(f"```\n{code}\n```")
    return "\n".join(parts)

from langchain_groq import ChatGroq

from agent.states import EnhancedPlan, File
from agent.tech_detector import TechStackDetector
from agent.knowledge_base.kb_manager import KnowledgeBaseManager


planning_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def planner_agent_v2(state: dict) -> dict:
    user_prompt = state["user_prompt"]
    user_edits = state.get("user_edits")
    
    detector = TechStackDetector()
    tech_detection = detector.detect(user_prompt)
    
    kb_manager = KnowledgeBaseManager()
    project_examples = {}
    
    for tech in tech_detection.get("all_techs", []):
        try:
            examples = kb_manager.query_single_tech(
                tech_stack=tech,
                query=user_prompt,
                n_results=3
            )
            if examples:
                project_examples[tech] = examples
        except Exception:
            pass

    examples_text = _format_examples(project_examples)
    
    prompt = _build_planning_prompt(user_prompt, tech_detection, examples_text, user_edits)
    
    response = planning_llm.with_structured_output(EnhancedPlan).invoke(prompt)
    
    if response is None:
        raise ValueError("Planner did not return a valid response")

    response.required_tech_stacks = tech_detection.get("all_techs", [])
    response.frontend_tech = tech_detection.get("frontend")
    response.backend_tech = tech_detection.get("backend")
    response.database_tech = tech_detection.get("database")
    response.deployment_tech = tech_detection.get("deployment")
    response.tech_stack_reasoning = tech_detection.get("reasoning", "")
    response.review_status = "pending"

    return {
        "plan": response,
        "tech_detection": tech_detection,
        "project_examples": project_examples,
        "stage": "plan_review"
    }


def _build_planning_prompt(
    user_prompt: str,
    tech_detection: dict,
    examples_text: str,
    user_edits: str = None
) -> str:
    edit_instruction = ""
    if user_edits:
        edit_instruction = f"""
USER REQUESTED CHANGES:
{user_edits}

Apply these changes to your plan."""

    return f"""You are the PLANNER agent. Create a complete project plan.

User Request: {user_prompt}
{edit_instruction}

DETECTED TECH STACKS: {tech_detection.get('all_techs', [])}
REASONING: {tech_detection.get('reasoning', '')}

{'PRODUCTION PATTERNS FROM KNOWLEDGE BASE:' + examples_text if examples_text else ''}

INSTRUCTIONS:
1. Create a comprehensive plan for the requested application
2. List ALL files needed with their exact paths and purposes
3. Use the detected tech stacks
4. Follow patterns from production examples if available
5. Be specific about file purposes

IMPORTANT:
- NO unnecessary comments in generated code
- Write like a 15+ year AI engineering expert
- Production-ready from day one"""


def _format_examples(project_examples: dict) -> str:
    if not project_examples:
        return ""
    
    parts = []
    for tech, examples in project_examples.items():
        if not examples:
            continue
        parts.append(f"\n### {tech.upper()} Examples:")
        for i, ex in enumerate(examples[:2], 1):
            code = ex.get("code", "")[:500]
            parts.append(f"Example {i}:\n```\n{code}\n```")
    
    return "\n".join(parts)

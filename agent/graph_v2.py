from langgraph.graph import StateGraph, END

from agent.planner_v2 import planner_agent_v2
from agent.architect_v2 import architect_agent_v2
from agent.coder_v2 import coder_agent_v2


def should_wait_for_plan_review(state: dict) -> str:
    stage = state.get("stage")
    user_action = state.get("plan_user_action")
    
    if stage != "plan_review":
        return "architect"
    
    if user_action == "approved":
        return "architect"
    elif user_action == "edit":
        return "planner"
    elif user_action == "regenerate":
        return "planner"
    
    return "wait"


def should_wait_for_task_review(state: dict) -> str:
    stage = state.get("stage")
    user_action = state.get("task_user_action")
    
    if stage != "task_review":
        return "coder"
    
    if user_action == "approved":
        return "coder"
    elif user_action == "edit":
        return "architect"
    elif user_action == "regenerate":
        return "architect"
    
    return "wait"


def should_continue_coding(state: dict) -> str:
    if state.get("status") == "DONE":
        return "complete"
    return "coder"


def build_graph_v2():
    """Build the full v2 graph starting from planner."""
    graph = StateGraph(dict)
    
    graph.add_node("planner", planner_agent_v2)
    graph.add_node("architect", architect_agent_v2)
    graph.add_node("coder", coder_agent_v2)
    
    graph.set_entry_point("planner")
    
    graph.add_conditional_edges(
        "planner",
        should_wait_for_plan_review,
        {
            "wait": END,
            "planner": "planner",
            "architect": "architect"
        }
    )
    
    graph.add_conditional_edges(
        "architect",
        should_wait_for_task_review,
        {
            "wait": END,
            "architect": "architect",
            "coder": "coder"
        }
    )
    
    graph.add_conditional_edges(
        "coder",
        should_continue_coding,
        {
            "coder": "coder",
            "complete": END
        }
    )
    
    return graph.compile()


def build_architect_graph():
    """Build a graph starting from architect (for resuming after plan approval)."""
    graph = StateGraph(dict)
    
    graph.add_node("architect", architect_agent_v2)
    graph.add_node("coder", coder_agent_v2)
    
    graph.set_entry_point("architect")
    
    graph.add_conditional_edges(
        "architect",
        should_wait_for_task_review,
        {
            "wait": END,
            "architect": "architect",
            "coder": "coder"
        }
    )
    
    graph.add_conditional_edges(
        "coder",
        should_continue_coding,
        {
            "coder": "coder",
            "complete": END
        }
    )
    
    return graph.compile()


def build_coder_graph():
    """Build a graph starting from coder (for resuming after task approval)."""
    graph = StateGraph(dict)
    
    graph.add_node("coder", coder_agent_v2)
    
    graph.set_entry_point("coder")
    
    graph.add_conditional_edges(
        "coder",
        should_continue_coding,
        {
            "coder": "coder",
            "complete": END
        }
    )
    
    return graph.compile()


agent_v2 = build_graph_v2()


if __name__ == "__main__":
    result = agent_v2.invoke(
        {"user_prompt": "Create a simple todo app with React frontend"},
        {"recursion_limit": 50}
    )
    print("Stage:", result.get("stage"))
    print("Plan:", result.get("plan"))

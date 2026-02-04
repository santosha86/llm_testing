"""
Simple LangGraph workflow for routing queries between SQL, CSV, and PDF agents.
Out-of-scope queries are rejected with a direct message.

Workflow Structure:
    START → router → sql_agent (if route=="sql") → END
                  → csv_agent (if route=="csv") → END
                  → pdf_agent (if route=="pdf") → END
                  → out_of_scope (if route=="out_of_scope") → END
                  → meta (if route=="meta") → END
"""

from typing import TypedDict, Literal, Optional, List, Any
from langgraph.graph import StateGraph, END

from .router import classify_query, handle_meta_question
from .memory import SharedMemory
from .agents.sql_agent import run_sql_agent
from .agents.csv_agent_wrapper import run_csv_agent
from .agents.pdf_agent_wrapper import run_pdf_agent
from .agents.math_agent import run_math_agent


class WorkflowState(TypedDict):
    """State passed through the workflow."""
    query: str
    session_id: str

    route: Optional[Literal["sql", "csv", "pdf", "math", "meta", "out_of_scope"]]

    content: Optional[str]
    response_time: Optional[str]
    sources: Optional[List[str]]
    table_data: Optional[dict]
    sql_query: Optional[str]

    # Disambiguation fields (for column selection)
    needs_disambiguation: Optional[bool]
    disambiguation_options: Optional[List[dict]]

    # Visualization configuration
    visualization: Optional[dict]

    error: Optional[str]


def router_node(state: WorkflowState) -> WorkflowState:
    """
    Classify the query and determine which agent to route to.
    Skips classification if route is already set (forced).
    Handles meta questions about conversation history.
    """
    # Check for meta questions FIRST (before forced route check)
    meta_result = handle_meta_question(state["query"], state["session_id"])
    if meta_result:
        return {
            **state,
            "route": "meta",
            "content": meta_result["content"],
            "response_time": meta_result["response_time"],
            "sources": meta_result["sources"]
        }

    # If route is already set (forced), skip classification
    if state.get("route") and state["route"] in ["sql", "csv", "pdf", "math"]:
        route = state["route"]
        print(f"[Router] Using forced route: {route}")
        # Store forced route for follow-up detection
        memory = SharedMemory.get_session(state["session_id"])
        memory.set_route(route)
        return state

    # Normal classification
    result = classify_query(state["query"], state["session_id"])
    route = result["route"]

    # Store route for follow-up detection (unless out_of_scope)
    if route != "out_of_scope":
        memory = SharedMemory.get_session(state["session_id"])
        memory.set_route(route)

    # Build state update
    state_update = {**state, "route": route}

    return state_update


def sql_agent_node(state: WorkflowState) -> WorkflowState:
    """
    Execute SQL agent and return response.
    """
    result = run_sql_agent(state["query"], state["session_id"])
    return {
        **state,
        "content": result.content,
        "response_time": result.response_time,
        "sources": result.sources,
        "table_data": result.table_data.to_dict() if result.table_data else None,
        "sql_query": result.sql_query,
        "needs_disambiguation": result.needs_disambiguation,
        "disambiguation_options": [opt.to_dict() for opt in result.disambiguation_options] if result.disambiguation_options else None,
        "visualization": result.visualization.to_dict() if result.visualization else None
    }


def csv_agent_node(state: WorkflowState) -> WorkflowState:
    """
    Execute CSV agent for vehicle dwell time data and return response.
    """
    result = run_csv_agent(state["query"], state["session_id"])
    return {
        **state,
        "content": result.content,
        "response_time": result.response_time,
        "sources": result.sources,
        "table_data": result.table_data.to_dict() if result.table_data else None,
        "sql_query": result.sql_query,
        "needs_disambiguation": result.needs_disambiguation,
        "disambiguation_options": [opt.to_dict() for opt in result.disambiguation_options] if result.disambiguation_options else None,
        "visualization": result.visualization.to_dict() if result.visualization else None
    }


def pdf_agent_node(state: WorkflowState) -> WorkflowState:
    """
    Execute PDF agent (non-streaming) and return response.
    """
    result = run_pdf_agent(state["query"], state["session_id"])
    return {
        **state,
        "content": result.content,
        "response_time": result.response_time,
        "sources": result.sources,
        "table_data": None,
        "sql_query": None,
        "needs_disambiguation": False,
        "disambiguation_options": None,
        "visualization": None
    }


def math_agent_node(state: WorkflowState) -> WorkflowState:
    """
    Execute Math agent for mathematical calculations and return response.
    """
    result = run_math_agent(state["query"], state["session_id"])
    return {
        **state,
        "content": result.content,
        "response_time": result.response_time,
        "sources": result.sources,
        "table_data": None,
        "sql_query": None,
        "needs_disambiguation": False,
        "disambiguation_options": None,
        "visualization": None
    }


def out_of_scope_node(state: WorkflowState) -> WorkflowState:
    """
    Return out-of-scope response when query is not related to our data sources.
    """
    return {
        **state,
        "content": "I can't answer this question because it's outside my data. I can help you with dispatch operations, waybills, vehicle dwell times, or Saudi Grid Code documents.",
        "response_time": "0s",
        "sources": ["System"],
        "table_data": None,
        "sql_query": None,
        "needs_disambiguation": False,
        "disambiguation_options": None,
        "visualization": None
    }


def meta_node(state: WorkflowState) -> WorkflowState:
    """
    Return meta response for conversational questions about the conversation.
    Content is already set by router_node - just pass through.
    """
    return state


def route_decision(state: WorkflowState) -> str:
    """
    Determine which agent to route to based on classification.
    """
    return state["route"]


def build_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("csv_agent", csv_agent_node)
    workflow.add_node("pdf_agent", pdf_agent_node)
    workflow.add_node("math_agent", math_agent_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    workflow.add_node("meta", meta_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional edges from router to agents
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "sql": "sql_agent",
            "csv": "csv_agent",
            "pdf": "pdf_agent",
            "math": "math_agent",
            "out_of_scope": "out_of_scope",
            "meta": "meta"
        }
    )

    # Add edges to END
    workflow.add_edge("sql_agent", END)
    workflow.add_edge("csv_agent", END)
    workflow.add_edge("pdf_agent", END)
    workflow.add_edge("math_agent", END)
    workflow.add_edge("out_of_scope", END)
    workflow.add_edge("meta", END)

    return workflow.compile()

dispatch_graph = build_workflow()


def run_workflow(query: str, session_id: str = "default", forced_route: str = None) -> dict:
    """
    Run the complete workflow.

    Args:
        query: User's natural language query
        session_id: Session ID for conversation memory
        forced_route: Optional route to force (bypasses router classification)

    Returns:
        Dictionary with content, response_time, sources, table_data, sql_query.
    """
    initial_state: WorkflowState = {
        "query": query,
        "session_id": session_id,
        "route": forced_route,  # Pre-set route if provided (bypasses router)
        "content": None,
        "response_time": None,
        "sources": None,
        "table_data": None,
        "sql_query": None,
        "needs_disambiguation": None,
        "disambiguation_options": None,
        "visualization": None,
        "error": None
    }

    result = dispatch_graph.invoke(initial_state)
    return result


def get_route_for_query(query: str, session_id: str = "default") -> str:
    """
    Get the route classification for a query without executing the full workflow.
    Useful for determining if streaming should be used.

    Args:
        query: User's query
        session_id: Session ID for conversation memory

    Returns:
        "sql", "csv", "pdf", or "out_of_scope"
    """
    result = classify_query(query, session_id)
    route = result["route"]

    # Store route for follow-up detection (unless out_of_scope)
    if route != "out_of_scope":
        memory = SharedMemory.get_session(session_id)
        memory.set_route(route)

    return route

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Any
import logging
import json
import uuid

from .utils import *
from .fixed_queries import FIXED_QUERIES
from .langgraph_workflow import run_workflow, get_route_for_query
from .agents.pdf_agent_wrapper import stream_pdf_agent
from .memory import SharedMemory

class EndpointFilter(logging.Filter):
    def filter(self, record):
        return "socket.io" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

app = FastAPI(title="SPB AI Dispatch Assistant API", version="1.0.0")

# CORS middleware for frontend access
# For production, replace ["*"] with specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComparisonItem(BaseModel):
    text: str
    type: str


class ProcessComparison(BaseModel):
    old_way: List[str]
    new_way: List[str]


class BusinessValueRow(BaseModel):
    metric: str
    before: str
    after: str


class KeyMetric(BaseModel):
    value: str
    label: str


class Capability(BaseModel):
    icon: str
    label: str


class AIAssistantOverview(BaseModel):
    process_comparison: ProcessComparison
    business_value: List[BusinessValueRow]
    key_metrics: List[KeyMetric]
    capabilities: List[Capability]
    language_support: str


class UsageStatsData(BaseModel):
    queries_processed: int
    user_satisfaction: str
    avg_response_time: str
    unique_users: int
    top_categories: dict


class QueryItem(BaseModel):
    text: str


class Category(BaseModel):
    id: str
    label: str
    icon: str
    queries: List[str]


class UserQuery(BaseModel):
    query: str
    session_id: Optional[str] = None
    route: Optional[str] = None


class TableData(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


class VisualizationConfig(BaseModel):
    should_visualize: bool
    chart_type: Optional[str] = None  # "bar", "line", "pie", "horizontal_bar", "grouped_bar"
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    y_axis_secondary: Optional[str] = None  # For grouped bar charts
    y_axis_list: Optional[List[str]] = None  # For 3+ numeric columns (wide format data)
    group_by: Optional[str] = None  # Column to group/pivot data by (for multi-category comparisons)
    title: Optional[str] = None


class DisambiguationOption(BaseModel):
    value: str
    display: str
    description: Optional[str] = None


class ClarificationOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None


class QueryResponse(BaseModel):
    content: str
    response_time: str
    sources: List[str]
    table_data: Optional[TableData] = None
    sql_query: Optional[str] = None
    needs_disambiguation: bool = False
    disambiguation_options: Optional[List[DisambiguationOption]] = None
    # Clarification fields for route selection
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    clarification_options: Optional[List[ClarificationOption]] = None
    # Visualization configuration
    visualization: Optional[VisualizationConfig] = None



AI_OVERVIEW_DATA = AIAssistantOverview(
    process_comparison=ProcessComparison(
        old_way=[
            "Multiple Excel files",
            "Wait for analysts",
            "Manual pivot tables",
            "2-4 hours response"
        ],
        new_way=[
            "Natural language",
            "2-3 second response",
            "Real-time data",
            "24/7 availability"
        ]
    ),
    business_value=[
        BusinessValueRow(metric="Response", before="2-4 hrs", after="2-3 sec"),
        BusinessValueRow(metric="Availability", before="Office hrs", after="24/7")
    ],
    key_metrics=[
        KeyMetric(value="50-60%", label="Faster"),
        KeyMetric(value="75%+", label="Accuracy"),
        KeyMetric(value="20-30%", label="Cost Savings"),
        KeyMetric(value="94%", label="Satisfaction")
    ],
    capabilities=[
        Capability(icon="search", label="Query & Search"),
        Capability(icon="chart", label="Analyze & Compare"),
        Capability(icon="lightbulb", label="Explain & Recommend"),
        Capability(icon="trending", label="Summarize & Forecast")
    ],
    language_support="English & Arabic Support"
)

USAGE_STATS_DATA = UsageStatsData(
    queries_processed=847,
    user_satisfaction="94%",
    avg_response_time="2.3s",
    unique_users=32,
    top_categories={
        "Operations & Dispatch": "35%",
        "Contractor Performance": "25%",
        "Management Reports": "20%",
        "Finance & Root Cause": "20%"
    }
)

# Get query keys from FIXED_QUERIES
QUERY_KEYS = list(FIXED_QUERIES.keys())

CATEGORIES_DATA = [
    Category(
        id="ops",
        label="Operations",
        icon="Truck",
        queries=[QUERY_KEYS[0], QUERY_KEYS[1]]  # Show today's dispatch, List all active
    ),
    Category(
        id="waybills",
        label="Waybills",
        icon="FileText",
        queries=[QUERY_KEYS[2], QUERY_KEYS[3]]  # Status of waybill, Details of waybill
    ),
    Category(
        id="contractors",
        label="Contractors",
        icon="Users",
        queries=[QUERY_KEYS[4], QUERY_KEYS[5]]  # Waybills for contractor, Contractor-wise list
    ),
    Category(
        id="Status Inquiry",
        label="Status Inquiry",
        icon="TrendingUp",
        queries=[QUERY_KEYS[6], QUERY_KEYS[7]]  # Route details, Waybills on route
    )
]

MOCK_RESPONSES = {
    "Which contractor caused most delays?": {
        "content": "Based on the analysis of Q3 data, **LogiTrans Corp** accounts for **32%** of all reported delays, primarily due to vehicle breakdown issues on the Northern Route.",
        "response_time": "0.8s",
        "sources": ["ODW Online", "SAP Finance"]
    },
    "Why was Waybill 784 late?": {
        "content": "**Waybill 784** was delayed by **45 minutes**. The root cause was identified as *Wait for Load* at the distribution center. The driver arrived at 08:00, but loading commenced at 08:45.",
        "response_time": "0.7s",
        "sources": ["ODW Online", "Telematics"]
    },
    "Summarize today's delayed dispatches": {
        "content": "Today, there are **14 delayed dispatches**. \n\n*   **Top Reason:** Traffic Congestion (8)\n*   **Secondary:** Documentation Issues (4)\n*   **Other:** Mechanical (2)\n\nAverage delay time: 22 minutes.",
        "response_time": "0.9s",
        "sources": ["ODW Online", "Fleet Management"]
    },
    "Show me pending reconciliations": {
        "content": "There are currently **23 pending reconciliations** awaiting approval.\n\n*   **Operations:** 12\n*   **Finance:** 8\n*   **Disputes:** 3\n\nMost are aged < 48 hours.",
        "response_time": "0.6s",
        "sources": ["SAP Finance", "ODW Online"]
    },
    "Top 5 delay reasons this week": {
        "content": "**Top 5 Delay Reasons (Current Week):**\n1.  Traffic / Route Congestion (35%)\n2.  Loading Dock Wait Time (22%)\n3.  Driver Unavailability (15%)\n4.  Documentation Errors (12%)\n5.  Vehicle Breakdown (10%)",
        "response_time": "0.8s",
        "sources": ["ODW Online", "Telematics"]
    },
    "Compare contractor performance Q3": {
        "content": "**Q3 Performance Summary:**\n\n*   **FastTrack Logistics:** 98% On-Time (Top Performer)\n*   **Global Freight:** 92% On-Time\n*   **LogiTrans Corp:** 85% On-Time (Requires Review)\n\nFastTrack has improved efficiency by 5% since Q2.",
        "response_time": "1.0s",
        "sources": ["ODW Online", "SAP Finance"]
    }
}



@app.get("/")
async def root():
    return {"message": "SPB AI Dispatch Assistant API", "version": "1.0.0"}


@app.get("/api/ai-overview", response_model=AIAssistantOverview)
async def get_ai_overview():
    """Get AI Assistant Overview data for the InfoPanel"""
    return AI_OVERVIEW_DATA


@app.get("/api/usage-stats", response_model=UsageStatsData)
async def get_usage_stats():
    """Get usage statistics data"""
    return USAGE_STATS_DATA


@app.get("/api/categories", response_model=List[Category])
async def get_categories():
    """Get query categories and their sample questions"""
    return CATEGORIES_DATA


@app.get("/api/categories/{category_id}/queries", response_model=List[str])
async def get_category_queries(category_id: str):
    """Get questions for a specific category"""
    for category in CATEGORIES_DATA:
        if category.id == category_id:
            return category.queries
    return []


@app.post("/api/query", response_model=QueryResponse)
async def process_query(user_query: UserQuery):
    """
    Process a user query through the LangGraph workflow.
    Routes to SQL agent for dispatch/waybill queries, PDF agent for document queries.
    Supports forced route from clarification flow.
    """
    query_text = user_query.query.strip()
    session_id = user_query.session_id or str(uuid.uuid4())
    forced_route = user_query.route  # Optional forced route from clarification

    if query_text in MOCK_RESPONSES:
        response_data = MOCK_RESPONSES[query_text]
        return QueryResponse(
            content=response_data["content"],
            response_time=response_data["response_time"],
            sources=response_data["sources"]
        )

    # Run through LangGraph workflow (with optional forced route)
    result = run_workflow(query_text, session_id, forced_route)

    # Build disambiguation options if present
    disambiguation_options = None
    if result.get("disambiguation_options"):
        disambiguation_options = [
            DisambiguationOption(**opt) for opt in result["disambiguation_options"]
        ]

    # Build clarification options if present
    clarification_options = None
    if result.get("clarification_options"):
        clarification_options = [
            ClarificationOption(**opt) for opt in result["clarification_options"]
        ]

    # Build visualization config if present
    visualization = None
    if result.get("visualization"):
        visualization = VisualizationConfig(**result["visualization"])

    return QueryResponse(
        content=result["content"] or "No response generated",
        response_time=result["response_time"] or "0s",
        sources=result["sources"] or ["System"],
        table_data=TableData(**result["table_data"]) if result["table_data"] else None,
        sql_query=result["sql_query"],
        needs_disambiguation=result.get("needs_disambiguation", False) or False,
        disambiguation_options=disambiguation_options,
        needs_clarification=result.get("needs_clarification", False) or False,
        clarification_message=result.get("clarification_message"),
        clarification_options=clarification_options,
        visualization=visualization
    )


@app.post("/api/query/stream")
async def process_query_stream(user_query: UserQuery):
    """
    Streaming endpoint for queries.
    Uses Server-Sent Events (SSE) format.
    - PDF queries stream with phases (planning, retrieval, reasoning, answer)
    - SQL/CSV queries return immediately as single SSE message
    - Clarify requests return options for user to select
    """
    query_text = user_query.query.strip()
    session_id = user_query.session_id or str(uuid.uuid4())

    # Use provided route or classify (avoid double classification from frontend)
    route = user_query.route or get_route_for_query(query_text, session_id)

    if route == "pdf":
        # Stream PDF agent response
        return StreamingResponse(
            stream_pdf_agent(query_text, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # For SQL/CSV/clarify, run synchronously and return as SSE format
        result = run_workflow(query_text, session_id, route)

        async def single_response():
            data = {
                "content": result["content"] or "No response generated",
                "done": True,
                "response_time": result["response_time"] or "0s",
                "sources": result["sources"] or ["System"],
                "table_data": result["table_data"],
                "sql_query": result["sql_query"],
                "needs_disambiguation": result.get("needs_disambiguation", False) or False,
                "disambiguation_options": result.get("disambiguation_options"),
                "needs_clarification": result.get("needs_clarification", False) or False,
                "clarification_message": result.get("clarification_message"),
                "clarification_options": result.get("clarification_options"),
                "visualization": result.get("visualization")
            }
            yield f"data: {json.dumps(data)}\n\n"

        return StreamingResponse(
            single_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )


class SessionClear(BaseModel):
    session_id: str


@app.post("/api/route")
async def get_query_route(user_query: UserQuery):
    """Return the route classification for a query (sql, csv, or pdf)."""
    session_id = user_query.session_id or "default"
    route = get_route_for_query(user_query.query.strip(), session_id)
    return {"route": route}


@app.post("/api/session/clear")
async def clear_session(request: SessionClear):
    """Clear conversation history for a session."""
    SharedMemory.clear_session(request.session_id)
    return {"status": "cleared", "session_id": request.session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
SQL Agent wrapper for the LangGraph workflow.
Handles both fixed queries and LLM-generated SQL.
"""

import time
import json
from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from langchain_core.messages import SystemMessage, HumanMessage

# Import from parent package using relative imports
from ..utils import (
    execute_sql,
    is_scalar_result,
    generate_scalar_response,
    generate_table_summary,
    model,
    system_prompt,
    DB_PATH
)
from ..fixed_queries import FIXED_QUERIES
from ..memory import SharedMemory
from ..column_disambiguator import (
    detect_sql_disambiguation,
    combine_query_with_disambiguation
)
from ..visualization_detector import detect_visualization, VisualizationConfig


# Key columns to extract for follow-up context
KEY_COLUMNS = [
    "Vendor Name", "Power Plant", "Power Plant Desc", "Plant Desc",
    "Route Code", "Route Desc", "Waybill Status Desc", "Contractor Name"
]


def _extract_result_context(result: dict) -> dict:
    """
    Extract key values from query result for follow-up context.
    This allows follow-up queries to reference entities like "this vendor", "that plant", etc.
    """
    if "error" in result or "rows" not in result:
        return None

    columns = result["columns"]
    rows = result["rows"]

    if not rows:
        return None

    # For single-row results, store all column values
    if len(rows) == 1:
        return {
            "type": "single_result",
            "values": {col: rows[0][i] for i, col in enumerate(columns)}
        }

    # For multi-row results, store count and key column values (first few rows)
    context = {
        "type": "multi_result",
        "count": len(rows),
        "key_values": {}
    }

    for i, col in enumerate(columns):
        if col in KEY_COLUMNS:
            # Store first 5 unique values for key columns
            unique_values = []
            seen = set()
            for row in rows[:10]:
                val = row[i]
                if val and val not in seen:
                    unique_values.append(val)
                    seen.add(val)
                if len(unique_values) >= 5:
                    break
            if unique_values:
                context["key_values"][col] = unique_values if len(unique_values) > 1 else unique_values[0]

    return context if context["key_values"] else None


@dataclass
class TableData:
    """Table data structure."""
    columns: List[str]
    rows: List[List[Any]]

    def to_dict(self) -> dict:
        return {"columns": self.columns, "rows": self.rows}


@dataclass
class DisambiguationOption:
    """Option for disambiguation."""
    value: str
    display: str
    description: str = ""

    def to_dict(self) -> dict:
        return {"value": self.value, "display": self.display, "description": self.description}


@dataclass
class SQLAgentResponse:
    """Response from SQL agent."""
    content: str
    response_time: str
    sources: List[str]
    table_data: Optional[TableData] = None
    sql_query: Optional[str] = None
    needs_disambiguation: bool = False
    disambiguation_options: Optional[List[DisambiguationOption]] = None
    visualization: Optional[VisualizationConfig] = None

    def to_dict(self) -> dict:
        result = {
            "content": self.content,
            "response_time": self.response_time,
            "sources": self.sources,
            "sql_query": self.sql_query,
            "needs_disambiguation": self.needs_disambiguation,
            "disambiguation_options": [opt.to_dict() for opt in self.disambiguation_options] if self.disambiguation_options else None
        }
        if self.table_data:
            result["table_data"] = self.table_data.to_dict()
        else:
            result["table_data"] = None
        if self.visualization:
            result["visualization"] = self.visualization.to_dict()
        else:
            result["visualization"] = None
        return result


def run_sql_agent(query: str, session_id: str = "default") -> SQLAgentResponse:
    """
    Run SQL agent on a query and return structured response.

    Args:
        query: User's natural language query
        session_id: Session ID for conversation memory

    Returns:
        SQLAgentResponse with content, table_data, etc.
    """
    start_time = time.time()
    query_text = query.strip()

    # Get conversation memory for follow-up questions
    memory = SharedMemory.get_session(session_id)
    history = memory.get()  # Get history BEFORE adding current message

    # CHECK 1: Is this a disambiguation response?
    if memory.has_pending_disambiguation():
        pending = memory.get_pending_disambiguation()
        original_query = pending["original_query"]
        ambiguous_term = pending["ambiguous_term"]
        selected_column = query_text  # User selected column

        # Combine: "total quantity for plant CP01" + "Requested Quantity"
        # → "total Requested Quantity for plant CP01"
        enhanced_query = combine_query_with_disambiguation(
            original_query, ambiguous_term, selected_column
        )
        print(f"[SQL Agent] Disambiguation resolved: '{original_query}' + '{selected_column}' → '{enhanced_query}'")

        memory.clear_pending_disambiguation()
        memory.add_user(enhanced_query)

        # Generate SQL with enhanced query
        response = _execute_generated_query(enhanced_query, history, start_time, memory)
        memory.add_ai(response.content)
        return response

    # CHECK 2: Does query have ambiguous columns?
    disambiguation = detect_sql_disambiguation(query_text)

    if disambiguation:
        # Store pending disambiguation
        memory.set_pending_disambiguation({
            "original_query": query_text,
            "ambiguous_term": disambiguation["ambiguous_term"]
        })

        elapsed_time = round(time.time() - start_time, 2)

        # Create disambiguation options
        options = [
            DisambiguationOption(
                value=opt["value"],
                display=opt["display"],
                description=opt.get("description", "")
            )
            for opt in disambiguation["options"]
        ]

        return SQLAgentResponse(
            content=disambiguation["question"],
            response_time=f"{elapsed_time}s",
            sources=["Waybills DB"],
            needs_disambiguation=True,
            disambiguation_options=options
        )

    # Normal flow: add message to history
    memory.add_user(query_text)

    # Check fixed queries first (faster path)
    if query_text in FIXED_QUERIES:
        response = _execute_fixed_query(query_text, start_time, memory)
        memory.add_ai(response.content)
        return response

    # Generate SQL with LLM (flexible path, pass history and memory for context)
    response = _execute_generated_query(query_text, history, start_time, memory)
    memory.add_ai(response.content)
    return response


def _execute_fixed_query(query_text: str, start_time: float, memory) -> SQLAgentResponse:
    """Execute a predefined fixed query."""
    sql_query = FIXED_QUERIES[query_text]
    result = execute_sql(DB_PATH, sql_query)
    elapsed_time = round(time.time() - start_time, 2)

    if "error" in result:
        return SQLAgentResponse(
            content=f'**Error executing query:**\n\n`{result["error"]}`',
            response_time=f"{elapsed_time}s",
            sources=["Waybills DB"],
            sql_query=sql_query
        )

    # Store result context for follow-up queries
    context = _extract_result_context(result)
    if context:
        memory.set_last_result_context(context)

    # Check for scalar result
    if is_scalar_result(result):
        scalar_value = result["rows"][0][0]
        column_name = result["columns"][0]
        natural_response = generate_scalar_response(query_text, column_name, scalar_value)
        return SQLAgentResponse(
            content=natural_response,
            response_time=f"{elapsed_time}s",
            sources=["Waybills DB"],
            sql_query=sql_query
        )

    # Table result
    row_count = len(result["rows"])
    summary = generate_table_summary(query_text, result["columns"], row_count)

    # Detect visualization
    visualization = detect_visualization(result["columns"], result["rows"], query_text)

    return SQLAgentResponse(
        content=summary,
        response_time=f"{elapsed_time}s",
        sources=["Waybills DB"],
        table_data=TableData(columns=result["columns"], rows=result["rows"]),
        sql_query=sql_query,
        visualization=visualization
    )


def _execute_generated_query(query_text: str, history: str, start_time: float, memory) -> SQLAgentResponse:
    """Generate SQL with LLM and execute."""
    try:
        # Get context summary from previous result for follow-up references
        context_summary = memory.get_context_summary()

        # Build prompt with conversation context for follow-up questions
        if history or context_summary:
            prompt_text = f"""Conversation History:
{history}

{context_summary}

Current Question: {query_text}

IMPORTANT: Use the conversation history AND the previous result context to understand references like "this vendor", "that contractor", "same plant", "this route", etc. Extract the actual values from the context above."""
        else:
            prompt_text = query_text

        # Generate SQL using LLM
        system_msg = SystemMessage(content=system_prompt)
        human_msg = HumanMessage(content=prompt_text)

        response = model.invoke([system_msg, human_msg])
        raw_content = response.content
        data = json.loads(raw_content)
        sql_query = data["sql"]
        print(sql_query)
        # Check if LLM returned unsupported request
        if sql_query.startswith("UNSUPPORTED_REQUEST:"):
            elapsed_time = round(time.time() - start_time, 2)
            message = sql_query.replace("UNSUPPORTED_REQUEST:", "").strip()
            return SQLAgentResponse(
                content=f"**Notice:** {message}",
                response_time=f"{elapsed_time}s",
                sources=["AI Assistant"]
            )

        # Execute the SQL query
        result = execute_sql(DB_PATH, sql_query)
        elapsed_time = round(time.time() - start_time, 2)

        if "error" in result:
            return SQLAgentResponse(
                content=f'**Error executing query:**\n\n`{result["error"]}`\n\n**Generated SQL:**\n```sql\n{sql_query}\n```',
                response_time=f"{elapsed_time}s",
                sources=["Waybills DB"],
                sql_query=sql_query
            )

        # Store result context for follow-up queries
        context = _extract_result_context(result)
        if context:
            memory.set_last_result_context(context)

        # Check for scalar result
        if is_scalar_result(result):
            scalar_value = result["rows"][0][0]
            column_name = result["columns"][0]
            natural_response = generate_scalar_response(query_text, column_name, scalar_value)
            return SQLAgentResponse(
                content=natural_response,
                response_time=f"{elapsed_time}s",
                sources=["Waybills DB"],
                sql_query=sql_query
            )

        # Table result
        row_count = len(result["rows"])
        summary = generate_table_summary(query_text, result["columns"], row_count)

        # Detect visualization
        visualization = detect_visualization(result["columns"], result["rows"], query_text)

        return SQLAgentResponse(
            content=summary,
            response_time=f"{elapsed_time}s",
            sources=["Waybills DB"],
            table_data=TableData(columns=result["columns"], rows=result["rows"]),
            sql_query=sql_query,
            visualization=visualization
        )

    except json.JSONDecodeError as e:
        elapsed_time = round(time.time() - start_time, 2)
        return SQLAgentResponse(
            content=f'**Error:** Failed to parse LLM response as JSON.\n\n{str(e)}',
            response_time=f"{elapsed_time}s",
            sources=["LLM"]
        )
    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        return SQLAgentResponse(
            content=f'**Error:** {str(e)}',
            response_time=f"{elapsed_time}s",
            sources=["System"]
        )

"""
CSV Agent wrapper - executes pandas code and returns structured data.
Similar pattern to SQL agent: LLM generates code, execute it, return table_data.
"""

import time
import json
import re
import pandas as pd
from typing import Optional, List, Any, Dict
from dataclasses import dataclass
from langchain_core.messages import SystemMessage, HumanMessage

from ..csv_agent import tabular_data
from ..utils import model
from ..memory import SharedMemory
from ..column_disambiguator import (
    detect_csv_disambiguation,
    combine_query_with_disambiguation
)
from ..visualization_detector import detect_visualization, VisualizationConfig


# Key columns to extract for follow-up context
CSV_KEY_COLUMNS = ["zone_name", "driver_id", "vehicle_name", "month"]


def _extract_csv_result_context(result, columns: List[str]) -> dict:
    """
    Extract key values from CSV query result for follow-up context.
    Works with DataFrame, Series, or scalar results.
    """
    if result is None:
        return None

    # Handle DataFrame result
    if isinstance(result, pd.DataFrame):
        if result.empty:
            return None

        rows = result.values.tolist()
        cols = list(result.columns)

        if len(rows) == 1:
            return {
                "type": "single_result",
                "values": {col: rows[0][i] for i, col in enumerate(cols)}
            }

        # Multi-row result
        context = {
            "type": "multi_result",
            "count": len(rows),
            "key_values": {}
        }

        for i, col in enumerate(cols):
            if col in CSV_KEY_COLUMNS:
                unique_values = list(set(str(r[i]) for r in rows[:10] if r[i] is not None))[:5]
                if unique_values:
                    context["key_values"][col] = unique_values if len(unique_values) > 1 else unique_values[0]

        return context if context["key_values"] else None

    # Handle Series result
    elif isinstance(result, pd.Series):
        if result.empty:
            return None

        if len(result) == 1:
            return {
                "type": "single_result",
                "values": {str(result.name) if result.name else "value": result.iloc[0]}
            }

        # Multi-value series (e.g., groupby result)
        return {
            "type": "multi_result",
            "count": len(result),
            "key_values": {str(result.name) if result.name else "value": list(result.head(5).to_dict().values())}
        }

    # Handle scalar result
    else:
        return {
            "type": "single_result",
            "values": {"result": result}
        }


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
class CSVAgentResponse:
    """Response from CSV agent."""
    content: str
    response_time: str
    sources: List[str]
    table_data: Optional[TableData] = None
    sql_query: Optional[str] = None  # Will contain pandas code
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


# System prompt for generating pandas code
CSV_SYSTEM_PROMPT = """You are a data analyst assistant. You have access to a pandas DataFrame called `df` with vehicle dwell time data.

DataFrame Info:
- Columns: {columns}
- Shape: {shape} (rows, columns)
- Sample data:
{sample}

Data Description:
This dataset contains vehicle movement records showing how long vehicles stayed inside different geofenced zones. Each row represents one visit: a vehicle (vehicle_name) driven by a driver (driver_id) enters a zone (zone_name) at entry_time, exits at exit_time, and the stay duration is captured in dwell_hrs and dwell_minutes.

### COLUMN DISAMBIGUATION (VERY IMPORTANT)

When user asks about:
- "stay time", "duration", "how long", "time spent", "مدة", "وقت" → Use `dwell_hrs` (hours) by default
  - Use `dwell_minutes` only if user specifically asks for minutes
- "vehicle", "truck", "car", "سيارة", "شاحنة" → Use `vehicle_name`
- "driver", "سائق" → Use `driver_id`
- "zone", "area", "location", "place", "geofence", "منطقة", "موقع" → Use `zone_name`
- "when", "date", "time", "متى", "تاريخ" → Use `entry_time` or `exit_time` or `month`
- "arrival", "entered", "entry", "دخول" → Use `entry_time`
- "departure", "left", "exit", "خروج" → Use `exit_time`

### Examples:
User: "average stay time for zone Hail 2"
Code: result = df[df['zone_name'].str.contains('Hail', case=False, na=False)]['dwell_hrs'].mean()

User: "how long did driver DRV000447 stay"
Code: result = df[df['driver_id'] == 'DRV000447']['dwell_hrs'].sum()

User: "total duration by zone"
Code: result = df.groupby('zone_name')['dwell_hrs'].sum().sort_values(ascending=False)

When the user asks a question:
1. Generate pandas code to answer it
2. The code should produce a result DataFrame, Series, or scalar value
3. Store the result in a variable called `result`

Respond with JSON only in this exact format:
{{"code": "result = df[df['driver_id'] == 'DRV001'].head(10)", "summary": "Retrieved 10 trips for driver DRV001"}}

Rules:
- Always use `df` as the DataFrame variable name
- Always store the final output in a variable called `result`
- Keep code simple and efficient (single line or multi-line is fine)
- Limit results to 100 rows max unless user asks for more
- For aggregations, use groupby, value_counts, agg, etc.
- For sorting, use sort_values()
- Select only relevant columns when possible to keep output clean
- Handle the query in Arabic or English
- IMPORTANT: For multiple conditions in DataFrame filtering, use `&` (and) and `|` (or), NOT Python's `and`/`or` keywords
  - CORRECT: df[(df['col1'] > 5) & (df['col2'] < 10)]
  - WRONG: df[(df['col1'] > 5) and (df['col2'] < 10)]"""


def run_csv_agent(query: str, session_id: str = "default") -> CSVAgentResponse:
    """
    Run CSV agent on vehicle dwell time data.

    Args:
        query: User's natural language query
        session_id: Session ID for conversation memory

    Returns:
        CSVAgentResponse with content, table_data, and metadata
    """
    start_time = time.time()

    # Get conversation memory for follow-up questions
    memory = SharedMemory.get_session(session_id)
    history = memory.get()  # Get history BEFORE adding current message

    # CHECK 1: Is this a disambiguation response?
    if memory.has_pending_disambiguation():
        pending = memory.get_pending_disambiguation()
        original_query = pending["original_query"]
        ambiguous_term = pending["ambiguous_term"]
        selected_column = query.strip()  # User selected column

        # Combine original query with selected column
        enhanced_query = combine_query_with_disambiguation(
            original_query, ambiguous_term, selected_column
        )
        print(f"[CSV Agent] Disambiguation resolved: '{original_query}' + '{selected_column}' → '{enhanced_query}'")

        memory.clear_pending_disambiguation()
        memory.add_user(enhanced_query)

        # Continue with enhanced query (handled in try block below)
        query = enhanced_query

    else:
        # CHECK 2: Does query have ambiguous columns?
        disambiguation = detect_csv_disambiguation(query)

        if disambiguation:
            # Store pending disambiguation
            memory.set_pending_disambiguation({
                "original_query": query,
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

            return CSVAgentResponse(
                content=disambiguation["question"],
                response_time=f"{elapsed_time}s",
                sources=["Vehicle Dwell Time Data"],
                needs_disambiguation=True,
                disambiguation_options=options
            )

        # Normal flow: add message to history
        memory.add_user(query)

    try:
        # Build context for LLM
        columns = list(tabular_data.columns)
        shape = tabular_data.shape
        sample = tabular_data.head(3).to_string()

        system_prompt = CSV_SYSTEM_PROMPT.format(
            columns=columns,
            shape=shape,
            sample=sample
        )

        # Get context summary from previous result for follow-up references
        context_summary = memory.get_context_summary()

        # Build user prompt with conversation history for follow-up questions
        if history or context_summary:
            user_prompt = f"""Conversation History:
{history}

{context_summary}

Current Question: {query}

IMPORTANT: Use the conversation history AND the previous result context to understand references like "this driver", "that zone", "same vehicle", "this zone", etc. Extract the actual values from the context above."""
        else:
            user_prompt = query

        # Get pandas code from LLM
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # Parse response
        print(response.content)
        response_text = response.content

        # Try to extract JSON from response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse LLM response as JSON: {response_text}")

        pandas_code = data.get("code", "")
        summary = data.get("summary", "Query executed successfully")

        if not pandas_code:
            raise ValueError("No code generated by LLM")

        # Clean up multi-line code with improper indentation
        # Replace newline + whitespace + dot with just dot (for method chaining)
        pandas_code = re.sub(r'\n\s+\.', '.', pandas_code)

        # Sanitize code to fix common anti-patterns (and/or -> &/|)
        pandas_code = _sanitize_pandas_code(pandas_code)

        # Execute code safely
        result = _execute_pandas_code(pandas_code, tabular_data)
        elapsed_time = round(time.time() - start_time, 2)

        # Store result context for follow-up queries
        context = _extract_csv_result_context(result, list(tabular_data.columns))
        if context:
            memory.set_last_result_context(context)

        # Convert result to table_data
        visualization = None

        if isinstance(result, pd.DataFrame):
            # Limit to 500 rows for display
            display_result = result.head(500)
            table_data_obj = TableData(
                columns=list(display_result.columns),
                rows=display_result.values.tolist()
            )
            row_count = len(result)
            if row_count > 500:
                content = f"{summary}\n\nShowing 500 of {row_count} records."
            else:
                content = f"{summary}\n\nFound {row_count} records."

            # Detect visualization for DataFrame
            visualization = detect_visualization(
                list(display_result.columns),
                display_result.values.tolist(),
                query
            )

        elif isinstance(result, pd.Series):
            # Convert Series to DataFrame for display
            display_result = result.head(500)
            # For Series with index, create two columns: index and value
            series_columns = [str(result.index.name) if result.index.name else "category", str(result.name) if result.name else "value"]
            series_rows = [[idx, val] for idx, val in zip(display_result.index.tolist(), display_result.values.tolist())]

            table_data_obj = TableData(
                columns=series_columns,
                rows=series_rows
            )
            content = f"{summary}\n\nFound {len(result)} values."

            # Detect visualization for Series (treat as category + value)
            visualization = detect_visualization(
                series_columns,
                series_rows,
                query
            )

        elif result is None:
            table_data_obj = None
            content = f"{summary}\n\nNo results returned."

        else:
            # Scalar result (count, sum, etc.)
            table_data_obj = None
            content = f"{summary}\n\n**Result:** {result}"

        # Store response in memory for follow-up questions
        memory.add_ai(content)

        return CSVAgentResponse(
            content=content,
            response_time=f"{elapsed_time}s",
            sources=["Vehicle Dwell Time Data"],
            table_data=table_data_obj,
            sql_query=pandas_code,
            visualization=visualization
        )

    except json.JSONDecodeError as e:
        elapsed_time = round(time.time() - start_time, 2)
        error_content = f"**Error:** Failed to parse LLM response. {str(e)}"
        memory.add_ai(error_content)
        return CSVAgentResponse(
            content=error_content,
            response_time=f"{elapsed_time}s",
            sources=["Error"]
        )
    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        error_content = f"**Error:** {str(e)}"
        memory.add_ai(error_content)
        return CSVAgentResponse(
            content=error_content,
            response_time=f"{elapsed_time}s",
            sources=["Error"]
        )


def _sanitize_pandas_code(code: str) -> str:
    """
    Sanitize pandas code to fix common LLM-generated anti-patterns.

    Fixes the "truth value of a Series is ambiguous" error by replacing
    Python's `and`/`or` operators with pandas' bitwise `&`/`|` operators
    in DataFrame boolean conditions.

    Args:
        code: Raw pandas code from LLM

    Returns:
        Sanitized code with fixed operators
    """
    # Replace 'and'/'or' with '&'/'|' in DataFrame boolean conditions
    # Pattern: ) and ( or ] and [ (common in DataFrame filtering)
    sanitized = code

    # Fix: (condition1) and (condition2) -> (condition1) & (condition2)
    sanitized = re.sub(r'\)\s+and\s+\(', ') & (', sanitized)
    sanitized = re.sub(r'\)\s+or\s+\(', ') | (', sanitized)

    # Fix: [condition1] and [condition2] -> [condition1] & [condition2]
    sanitized = re.sub(r'\]\s+and\s+\[', '] & [', sanitized)
    sanitized = re.sub(r'\]\s+or\s+\[', '] | [', sanitized)

    # Fix: condition1 and condition2 within brackets (without parentheses)
    # e.g., df[df['a'] > 5 and df['b'] < 10] -> df[(df['a'] > 5) & (df['b'] < 10)]
    sanitized = re.sub(r"(\w+\s*[<>=!]+\s*\S+)\s+and\s+(\S+\s*[<>=!]+)", r'(\1) & (\2)', sanitized)
    sanitized = re.sub(r"(\w+\s*[<>=!]+\s*\S+)\s+or\s+(\S+\s*[<>=!]+)", r'(\1) | (\2)', sanitized)

    if sanitized != code:
        print(f"[CSV Agent] Sanitized code: replaced 'and'/'or' with '&'/'|'")

    return sanitized


def _execute_pandas_code(code: str, df: pd.DataFrame) -> Any:
    """
    Safely execute pandas code and return result.

    Args:
        code: Pandas code to execute
        df: DataFrame to operate on

    Returns:
        Result of the code execution (DataFrame, Series, or scalar)
    """
    # Create execution environment with limited scope
    safe_globals = {
        "df": df.copy(),  # Use copy to prevent modifications to original
        "pd": pd,
        "__builtins__": {
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "list": list,
            "dict": dict,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "True": True,
            "False": False,
            "None": None,
        }
    }
    safe_locals = {}

    # Execute code
    exec(code, safe_globals, safe_locals)

    # Return result
    return safe_locals.get("result", None)

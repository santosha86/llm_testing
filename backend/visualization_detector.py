"""
Visualization detector for automatic chart type selection.
Analyzes query results and determines the best visualization type.
"""

from typing import List, Any, Optional, Dict
from dataclasses import dataclass
import re


def _is_numeric_value(val: Any) -> bool:
    """Check if value is numeric (int, float, or numeric string like '477')."""
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, str):
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False
    return False


@dataclass
class VisualizationConfig:
    """Configuration for chart visualization."""
    should_visualize: bool
    chart_type: Optional[str]  # "bar", "line", "pie", "horizontal_bar", "grouped_bar"
    x_axis: Optional[str]
    y_axis: Optional[str]
    y_axis_secondary: Optional[str]  # For grouped bar charts (2 numeric columns)
    y_axis_list: Optional[List[str]]  # For 3+ numeric columns (wide format data)
    group_by: Optional[str]  # Column to group/pivot data by (for multi-category comparisons)
    title: Optional[str]

    def to_dict(self) -> dict:
        return {
            "should_visualize": self.should_visualize,
            "chart_type": self.chart_type,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "y_axis_secondary": self.y_axis_secondary,
            "y_axis_list": self.y_axis_list,
            "group_by": self.group_by,
            "title": self.title
        }


# Time-related columns that suggest line charts
TIME_COLUMNS = [
    "date", "month", "year", "day", "week", "quarter",
    "scheduled date", "actual date", "created date", "creation date",
    "entry_time", "exit_time", "timestamp",
    "scheduled_date", "actual_date", "created_date",
    # Arabic
    "تاريخ", "شهر", "سنة", "يوم"
]

# Category columns that suggest bar/pie charts
CATEGORY_COLUMNS = [
    "vendor name", "vendor", "contractor", "contractor name",
    "status", "waybill status", "waybill status desc",
    "plant", "power plant", "power plant desc", "plant desc",
    "fuel type", "fuel", "route", "route code", "route desc",
    "zone_name", "zone", "driver_id", "driver", "vehicle_name", "vehicle",
    # Arabic
    "مقاول", "حالة", "مصنع", "منطقة", "سائق", "سيارة"
]

# Value/numeric columns that should be on Y-axis
VALUE_COLUMNS = [
    "count", "count(*)", "sum", "total", "avg", "average", "mean",
    "quantity", "requested quantity", "actual quantity",
    "cost", "price", "amount", "value",
    "dwell_hrs", "dwell_minutes", "duration", "hours", "minutes",
    # Arabic
    "عدد", "مجموع", "كمية", "متوسط"
]

# Proportion query keywords that suggest pie charts
PROPORTION_KEYWORDS = [
    "by status", "by type", "by category", "distribution",
    "breakdown", "split", "percentage", "proportion",
    "حسب الحالة", "توزيع"
]

# Query keywords that indicate user wants RAW DATA (no visualization)
NO_VISUALIZATION_KEYWORDS = [
    # List/detail queries
    "list", "show all", "give me all", "display all", "all records",
    "details", "detail", "information", "info",
    "records", "entries", "items",
    "waybill number", "specific", "particular",
    # Interrogative queries asking for specific items
    "which", "what are the", "what is the", "show me the",
    # Assignment/relationship queries
    "assigned to", "belongs to", "related to", "for contractor", "for vendor",
    # Lookup queries
    "find", "search", "lookup", "get the",
    # Arabic
    "قائمة", "كل", "تفاصيل", "سجلات", "أي", "ما هي"
]

# Query keywords that indicate user wants AGGREGATED view (visualization)
VISUALIZATION_KEYWORDS = [
    "count", "total", "sum", "average", "how many",
    "compare", "comparison", "versus", "vs",
    "breakdown", "distribution", "split",
    "trend", "over time", "monthly", "daily", "weekly", "yearly",
    "top", "bottom", "highest", "lowest", "best", "worst", "rank",
    # Arabic
    "عدد", "مجموع", "مقارنة", "توزيع", "أعلى", "أقل"
]

# Explicit chart request keywords (HIGHEST PRIORITY - always show visualization)
EXPLICIT_CHART_KEYWORDS = [
    "show in chart", "show chart", "in chart", "as chart",
    "visualize", "visualization", "graph", "plot",
    "show in graph", "as graph", "display chart",
    # Arabic
    "رسم بياني", "مخطط"
]


def _normalize_column(col: str) -> str:
    """Normalize column name for comparison."""
    return col.lower().strip().replace("_", " ").replace("-", " ")


def _is_time_column(col: str) -> bool:
    """Check if column is time-related."""
    normalized = _normalize_column(col)
    return any(time_col in normalized for time_col in TIME_COLUMNS)


def _is_category_column(col: str) -> bool:
    """Check if column is category-related."""
    normalized = _normalize_column(col)
    return any(cat_col in normalized for cat_col in CATEGORY_COLUMNS)


def _is_value_column(col: str) -> bool:
    """Check if column is a value/numeric column."""
    normalized = _normalize_column(col)
    return any(val_col in normalized for val_col in VALUE_COLUMNS)


def _is_proportion_query(query: str) -> bool:
    """Check if query suggests proportion/distribution visualization."""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in PROPORTION_KEYWORDS)


def _should_skip_visualization(query: str) -> bool:
    """Check if query indicates user wants raw data, not a chart."""
    query_lower = query.lower()

    # HIGHEST PRIORITY: Explicit chart request - always visualize
    for keyword in EXPLICIT_CHART_KEYWORDS:
        if keyword in query_lower:
            return False  # User explicitly wants a chart

    # Check for visualization keywords (high priority)
    for keyword in VISUALIZATION_KEYWORDS:
        if keyword in query_lower:
            return False  # User wants visualization

    # Check for no-visualization keywords
    for keyword in NO_VISUALIZATION_KEYWORDS:
        if keyword in query_lower:
            return True  # User wants raw data

    return False  # Default: allow visualization based on data structure


def _detect_column_types(columns: List[str]) -> Dict[str, List[str]]:
    """Categorize columns by type."""
    result = {
        "time": [],
        "category": [],
        "value": [],
        "other": []
    }

    for col in columns:
        if _is_time_column(col):
            result["time"].append(col)
        elif _is_value_column(col):
            result["value"].append(col)
        elif _is_category_column(col):
            result["category"].append(col)
        else:
            result["other"].append(col)

    return result


def _generate_title(query: str, chart_type: str, x_axis: str, y_axis: str) -> str:
    """Generate a chart title based on query and axes."""
    # Try to extract meaningful title from query
    query_lower = query.lower()

    # Common patterns
    if "by" in query_lower:
        # "waybills by status" -> "Waybills by Status"
        parts = query.split("by")
        if len(parts) >= 2:
            return f"{parts[0].strip().title()} by {parts[1].strip().title()}"

    if "per" in query_lower:
        parts = query.split("per")
        if len(parts) >= 2:
            return f"{parts[0].strip().title()} per {parts[1].strip().title()}"

    if "for" in query_lower and any(word in query_lower for word in ["total", "count", "sum", "average"]):
        return f"{y_axis} by {x_axis}"

    # Default title
    return f"{y_axis} by {x_axis}"


def _no_visualization() -> VisualizationConfig:
    """Return a config indicating no visualization."""
    return VisualizationConfig(
        should_visualize=False,
        chart_type=None,
        x_axis=None,
        y_axis=None,
        y_axis_secondary=None,
        y_axis_list=None,
        group_by=None,
        title=None
    )


def detect_visualization(
    columns: List[str],
    rows: List[List[Any]],
    query: str
) -> VisualizationConfig:
    """
    Detect the best visualization type for query results.

    PRIMARY: Uses data-type detection (string + number = category + value)
    SECONDARY: Uses column name patterns for time-based detection

    Args:
        columns: List of column names
        rows: List of data rows
        query: Original user query

    Returns:
        VisualizationConfig with chart type and axis information
    """
    # No visualization for empty results
    if not columns or not rows:
        return _no_visualization()

    # Check query intent - skip visualization for "list", "details", etc.
    if _should_skip_visualization(query):
        return _no_visualization()

    num_columns = len(columns)
    num_rows = len(rows)

    # CASE 1: Single row result - no chart needed (e.g., "highest vendor", "lowest count")
    if num_rows == 1:
        return _no_visualization()

    # CASE 2: Single column, multiple rows - no good visualization
    if num_columns == 1:
        return _no_visualization()

    # Get first row for data type detection
    first_row = rows[0] if rows else []

    # ===========================================
    # PRIMARY DETECTION: Data-type based (most reliable)
    # ===========================================

    # CASE 3: Two columns - String + Number = Category + Value → Bar/Pie
    # NOTE: First check if there are multiple numeric columns - if so, skip to CASE 4
    if num_columns >= 2 and len(first_row) >= 2:
        first_val = first_row[0]
        second_val = first_row[1]

        first_is_string = isinstance(first_val, str)
        second_is_number = _is_numeric_value(second_val)  # Use helper for string numbers

        # Count ALL numeric columns to decide if this is CASE 3 or CASE 4
        if first_is_string and second_is_number:
            numeric_col_count = sum(1 for i in range(1, len(first_row)) if _is_numeric_value(first_row[i]))

            # If 2+ numeric columns exist, skip CASE 3 and let CASE 4 handle it
            if numeric_col_count >= 2:
                pass  # Fall through to CASE 4
            else:
                # Only 1 numeric column - handle in CASE 3
                x_axis = columns[0]
                y_axis = columns[1]

                # Check if first column is time-related → Line chart
                if _is_time_column(x_axis):
                    return VisualizationConfig(
                        should_visualize=True,
                        chart_type="line",
                        x_axis=x_axis,
                        y_axis=y_axis,
                        y_axis_secondary=None,
                        y_axis_list=None,
                        group_by=None,
                        title=_generate_title(query, "line", x_axis, y_axis)
                    )

                # Determine bar/pie based on row count
                if num_rows > 10:
                    chart_type = "horizontal_bar"
                elif num_rows <= 6:
                    chart_type = "pie"
                else:
                    chart_type = "bar"

                return VisualizationConfig(
                    should_visualize=True,
                    chart_type=chart_type,
                    x_axis=x_axis,
                    y_axis=y_axis,
                    y_axis_secondary=None,
                    y_axis_list=None,
                    group_by=None,
                    title=_generate_title(query, chart_type, x_axis, y_axis)
                )

    # CASE 4: String + Multiple Numbers → Grouped Bar with all numeric columns
    # Handles wide-format data like: Vendor | cancelled | expired | rejected
    if num_columns >= 3 and len(first_row) >= 3:
        first_val = first_row[0]
        first_is_string = isinstance(first_val, str)

        # Collect ALL numeric columns after the first column
        # Uses _is_numeric_value to handle strings like "477" from SQL
        numeric_columns = []
        for i in range(1, min(num_columns, len(first_row))):
            if _is_numeric_value(first_row[i]):
                numeric_columns.append(columns[i])

        if first_is_string and len(numeric_columns) >= 2:
            x_axis = columns[0]

            # Check if first column is time-related → Line chart
            if _is_time_column(x_axis):
                return VisualizationConfig(
                    should_visualize=True,
                    chart_type="line",
                    x_axis=x_axis,
                    y_axis=numeric_columns[0],
                    y_axis_secondary=numeric_columns[1] if len(numeric_columns) >= 2 else None,
                    y_axis_list=numeric_columns if len(numeric_columns) > 2 else None,
                    group_by=None,
                    title=_generate_title(query, "line", x_axis, " vs ".join(numeric_columns))
                )

            # Grouped bar for 2+ numeric columns
            # Use horizontal layout when many rows for readability
            chart_type = "horizontal_grouped_bar" if num_rows > 10 else "grouped_bar"
            return VisualizationConfig(
                should_visualize=True,
                chart_type=chart_type,
                x_axis=x_axis,
                y_axis=numeric_columns[0],
                y_axis_secondary=numeric_columns[1] if len(numeric_columns) == 2 else None,
                y_axis_list=numeric_columns if len(numeric_columns) > 2 else None,
                group_by=None,
                title=f"Comparison by {x_axis}"
            )

    # CASE 4.5: Three columns - String + String + Number
    # Detect if first column is a category for grouped comparison
    # Example: status | contractor | count → grouped bar with status as groups
    if num_columns >= 3 and len(first_row) >= 3:
        first_val = first_row[0]
        second_val = first_row[1]
        third_val = first_row[2]

        first_is_string = isinstance(first_val, str)
        second_is_string = isinstance(second_val, str)
        third_is_number = isinstance(third_val, (int, float))

        if first_is_string and second_is_string and third_is_number:
            # Count unique values in first column to detect if it's a grouping category
            unique_first_values = len(set(row[0] for row in rows))
            unique_second_values = len(set(row[1] for row in rows))

            x_axis = columns[1]  # Second column (e.g., contractor)
            y_axis = columns[2]  # Third column (e.g., count)

            # If first column has few unique values (<=10), it's likely a category to group by
            # This enables multi-category comparison (e.g., cancelled vs expired vs rejected)
            if unique_first_values <= 10 and unique_first_values > 1:
                # Use horizontal layout when many x-axis items for readability
                chart_type = "horizontal_grouped_bar" if unique_second_values > 10 else "grouped_bar"
                return VisualizationConfig(
                    should_visualize=True,
                    chart_type=chart_type,
                    x_axis=x_axis,
                    y_axis=y_axis,
                    y_axis_secondary=None,
                    y_axis_list=None,
                    group_by=columns[0],  # First column is the grouping category
                    title=f"{y_axis} by {x_axis} grouped by {columns[0]}"
                )

            # Fallback: simple bar/pie chart without grouping
            if num_rows > 10:
                chart_type = "horizontal_bar"
            elif num_rows <= 6:
                chart_type = "pie"
            else:
                chart_type = "bar"

            return VisualizationConfig(
                should_visualize=True,
                chart_type=chart_type,
                x_axis=x_axis,
                y_axis=y_axis,
                y_axis_secondary=None,
                y_axis_list=None,
                group_by=None,
                title=_generate_title(query, chart_type, x_axis, y_axis)
            )

    # ===========================================
    # SECONDARY DETECTION: Column name patterns
    # ===========================================

    # Analyze column types by name
    col_types = _detect_column_types(columns)

    # CASE 5: Time column detected by name → Line chart
    if col_types["time"]:
        x_axis = col_types["time"][0]
        y_axis = col_types["value"][0] if col_types["value"] else columns[1] if num_columns > 1 else None
        if y_axis:
            return VisualizationConfig(
                should_visualize=True,
                chart_type="line",
                x_axis=x_axis,
                y_axis=y_axis,
                y_axis_secondary=col_types["value"][1] if len(col_types["value"]) > 1 else None,
                y_axis_list=None,
                group_by=None,
                title=_generate_title(query, "line", x_axis, y_axis)
            )

    # CASE 6: Category column detected by name
    if col_types["category"] and num_columns >= 2:
        x_axis = col_types["category"][0]
        y_axis = col_types["value"][0] if col_types["value"] else columns[1]

        if num_rows > 10:
            chart_type = "horizontal_bar"
        elif num_rows <= 6:
            chart_type = "pie"
        else:
            chart_type = "bar"

        return VisualizationConfig(
            should_visualize=True,
            chart_type=chart_type,
            x_axis=x_axis,
            y_axis=y_axis,
            y_axis_secondary=None,
            y_axis_list=None,
            group_by=None,
            title=_generate_title(query, chart_type, x_axis, y_axis)
        )

    # Default: No visualization for complex or unclear data
    return _no_visualization()

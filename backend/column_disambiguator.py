"""
Column Disambiguator module for SQL and CSV agents.
Detects ambiguous column references in user queries and provides options for clarification.
"""

from typing import Optional, Dict, List

# Ambiguous term mappings for SQL (waybills database)
SQL_AMBIGUOUS_TERMS = {
    "quantity": {
        "columns": ["Requested Quantity", "Actual Quantity"],
        "question": "Which quantity do you mean?",
        "descriptions": {
            "Requested Quantity": "The quantity requested for delivery",
            "Actual Quantity": "The actual delivered quantity"
        }
    },
    "الكمية": {  # Arabic for "quantity"
        "columns": ["Requested Quantity", "Actual Quantity"],
        "question": "أي كمية تقصد؟",
        "descriptions": {
            "Requested Quantity": "الكمية المطلوبة للتسليم",
            "Actual Quantity": "الكمية الفعلية المسلمة"
        }
    },
    "date": {
        "columns": ["Scheduled Date", "Actual Date", "Loading Date"],
        "question": "Which date do you mean?",
        "descriptions": {
            "Scheduled Date": "The scheduled delivery date",
            "Actual Date": "The actual delivery date",
            "Loading Date": "The date when loading occurred"
        }
    },
    "تاريخ": {  # Arabic for "date"
        "columns": ["Scheduled Date", "Actual Date", "Loading Date"],
        "question": "أي تاريخ تقصد؟",
        "descriptions": {
            "Scheduled Date": "تاريخ التسليم المجدول",
            "Actual Date": "تاريخ التسليم الفعلي",
            "Loading Date": "تاريخ التحميل"
        }
    },
    "name": {
        "columns": ["Contractor Name", "Plant Name", "Power Plant Name"],
        "question": "Which name do you mean?",
        "descriptions": {
            "Contractor Name": "The name of the contractor/vendor",
            "Plant Name": "The source plant name",
            "Power Plant Name": "The destination power plant"
        }
    },
    "اسم": {  # Arabic for "name"
        "columns": ["Contractor Name", "Plant Name", "Power Plant Name"],
        "question": "أي اسم تقصد؟",
        "descriptions": {
            "Contractor Name": "اسم المقاول",
            "Plant Name": "اسم المصنع المصدر",
            "Power Plant Name": "اسم محطة الطاقة"
        }
    },
    "status": {
        "columns": ["Waybill Status", "Delivery Status"],
        "question": "Which status do you mean?",
        "descriptions": {
            "Waybill Status": "Current status of the waybill",
            "Delivery Status": "Delivery completion status"
        }
    },
    "حالة": {  # Arabic for "status"
        "columns": ["Waybill Status", "Delivery Status"],
        "question": "أي حالة تقصد؟",
        "descriptions": {
            "Waybill Status": "حالة بوليصة الشحن الحالية",
            "Delivery Status": "حالة اكتمال التسليم"
        }
    }
}

# Ambiguous term mappings for CSV (vehicle dwell time data)
CSV_AMBIGUOUS_TERMS = {
    "duration": {
        "columns": ["dwell_hrs", "dwell_minutes"],
        "question": "Which duration format do you prefer?",
        "descriptions": {
            "dwell_hrs": "Duration in hours (e.g., 2.5 hours)",
            "dwell_minutes": "Duration in minutes (e.g., 150 minutes)"
        }
    },
    "مدة": {  # Arabic for "duration"
        "columns": ["dwell_hrs", "dwell_minutes"],
        "question": "أي صيغة للمدة تفضل؟",
        "descriptions": {
            "dwell_hrs": "المدة بالساعات",
            "dwell_minutes": "المدة بالدقائق"
        }
    },
    "time": {
        "columns": ["entry_time", "exit_time"],
        "question": "Which time do you mean?",
        "descriptions": {
            "entry_time": "When the vehicle entered the zone",
            "exit_time": "When the vehicle exited the zone"
        }
    },
    "وقت": {  # Arabic for "time"
        "columns": ["entry_time", "exit_time"],
        "question": "أي وقت تقصد؟",
        "descriptions": {
            "entry_time": "وقت دخول السيارة للمنطقة",
            "exit_time": "وقت خروج السيارة من المنطقة"
        }
    }
}


def is_already_specific(query: str, term: str, columns: List[str]) -> bool:
    """
    Check if query already specifies which column.
    e.g., "requested quantity" is specific, "quantity" alone is not.
    """
    query_lower = query.lower()
    for col in columns:
        col_lower = col.lower()
        # Check if the full column name is in the query
        if col_lower in query_lower:
            return True
        # Check for common variations
        if col_lower.replace("_", " ") in query_lower:
            return True
    return False


def detect_sql_disambiguation(query: str) -> Optional[Dict]:
    """
    Detect if a SQL query has ambiguous column references.

    Args:
        query: User's natural language query

    Returns:
        Dict with disambiguation info if ambiguity found, None otherwise
    """
    query_lower = query.lower()

    for term, info in SQL_AMBIGUOUS_TERMS.items():
        if term in query_lower:
            # Check if user already specified which column
            if not is_already_specific(query_lower, term, info["columns"]):
                return {
                    "ambiguous_term": term,
                    "question": info["question"],
                    "options": [
                        {
                            "value": col,
                            "display": col,
                            "description": info["descriptions"].get(col, "")
                        }
                        for col in info["columns"]
                    ]
                }
    return None


def detect_csv_disambiguation(query: str) -> Optional[Dict]:
    """
    Detect if a CSV query has ambiguous column references.

    Args:
        query: User's natural language query

    Returns:
        Dict with disambiguation info if ambiguity found, None otherwise
    """
    query_lower = query.lower()

    for term, info in CSV_AMBIGUOUS_TERMS.items():
        if term in query_lower:
            # Check if user already specified which column
            if not is_already_specific(query_lower, term, info["columns"]):
                return {
                    "ambiguous_term": term,
                    "question": info["question"],
                    "options": [
                        {
                            "value": col,
                            "display": col,
                            "description": info["descriptions"].get(col, "")
                        }
                        for col in info["columns"]
                    ]
                }
    return None


def combine_query_with_disambiguation(original_query: str, ambiguous_term: str, selected_column: str) -> str:
    """
    Combine the original query with the user's disambiguation choice.

    Args:
        original_query: The original user query
        ambiguous_term: The term that was ambiguous (e.g., "quantity")
        selected_column: The column the user selected (e.g., "Requested Quantity")

    Returns:
        Enhanced query with the specific column reference
    """
    # Replace the ambiguous term with the selected column
    # Case-insensitive replacement
    query_lower = original_query.lower()
    term_lower = ambiguous_term.lower()

    # Find the position of the ambiguous term
    pos = query_lower.find(term_lower)
    if pos != -1:
        # Replace with the selected column
        enhanced_query = original_query[:pos] + selected_column + original_query[pos + len(ambiguous_term):]
        return enhanced_query

    # If term not found directly, append the column specification
    return f"{original_query} (using {selected_column})"

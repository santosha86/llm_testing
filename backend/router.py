"""
LLM-based query router for classifying user queries.
Routes to SQL agent (dispatch/waybill data), CSV agent (vehicle dwell time), PDF agent (document queries),
or returns "clarify" when uncertain to ask user for clarification.
"""

import json
from typing import Union, Dict, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from .memory import SharedMemory
from .column_disambiguator import SQL_AMBIGUOUS_TERMS, CSV_AMBIGUOUS_TERMS


# CSV routing keywords - explicit column names and keywords that should route to CSV agent
CSV_ROUTE_KEYWORDS = [
    # Exact column names
    "driver_id", "vehicle_name", "zone_name", "dwell_hrs", "dwell_minutes",
    "entry_time", "exit_time",

    # Common variations (English)
    "dwell", "dwell time", "stay time", "stay duration",
    "zone", "zones", "geofence", "geofences",
    "driver", "drivers",
    "vehicle", "vehicles", "truck", "trucks",
    "trip", "trips", "visit", "visits",

    # Arabic variations
    "سائق", "سائقين",  # driver, drivers
    "منطقة", "مناطق",  # zone, zones
    "سيارة", "سيارات", "شاحنة",  # vehicle, vehicles, truck
    "رحلة", "رحلات",  # trip, trips
]


# Math routing keywords - terms that indicate mathematical calculations
MATH_ROUTE_KEYWORDS = [
    # English keywords
    "calculate", "compute", "math", "calculation",
    "add", "subtract", "multiply", "divide",
    "sum", "difference", "product", "quotient",
    "plus", "minus", "times", "divided by",
    "square root", "sqrt", "power", "exponent",
    "percent", "percentage", "modulo", "remainder",
    "factorial", "logarithm", "log", "sine", "cosine", "tangent",
    "sin", "cos", "tan",

    # Arabic keywords
    "حساب", "احسب", "حسابات",  # calculate, compute, calculations
    "جمع", "طرح", "ضرب", "قسمة",  # add, subtract, multiply, divide
    "زائد", "ناقص", "مضروب", "مقسوم",  # plus, minus, times, divided
    "الجذر", "جذر تربيعي",  # root, square root
    "النسبة المئوية", "المئوية",  # percentage
    "أس", "قوة",  # power, exponent
]


# Meta question patterns for conversational queries about the conversation itself
META_PATTERNS = [
    "last question", "previous question", "what did i ask",
    "my question", "asked before", "earlier question",
    "what was my", "what i asked"
]


def handle_meta_question(query: str, session_id: str) -> Optional[Dict]:
    """
    Handle meta questions about conversation history.

    Args:
        query: User's query
        session_id: Session ID for conversation memory

    Returns:
        Dict with meta response if it's a meta question, None otherwise
    """
    q = query.lower()

    if any(pattern in q for pattern in META_PATTERNS):
        memory = SharedMemory.get_session(session_id)
        messages = memory.get_messages()
        user_questions = [m.content for m in messages if isinstance(m, HumanMessage)]

        if user_questions:
            last_q = user_questions[-1]
            return {
                "route": "meta",
                "content": f"Your last question was: \"{last_q}\"",
                "response_time": "0s",
                "sources": ["Conversation History"]
            }
        else:
            return {
                "route": "meta",
                "content": "This is your first question in our conversation.",
                "response_time": "0s",
                "sources": ["Conversation History"]
            }
    return None


def detect_route_from_column_terms(query: str) -> Optional[str]:
    """
    Detect route based on column terms and keywords in query.
    This helps route queries directly to the appropriate agent without needing LLM classification.

    Args:
        query: User's natural language query

    Returns:
        "sql" if SQL column terms detected,
        "csv" if CSV column terms/keywords detected,
        "math" if math keywords detected,
        None if no column terms found
    """
    query_lower = query.lower()

    # CHECK MATH KEYWORDS FIRST (explicit math operations and terms)
    # These are unambiguous and should always route to math agent
    for keyword in MATH_ROUTE_KEYWORDS:
        if keyword in query_lower:
            return "math"

    # CHECK CSV KEYWORDS (explicit CSV column names and terms)
    # These are unambiguous and should always route to CSV
    for keyword in CSV_ROUTE_KEYWORDS:
        if keyword in query_lower:
            return "csv"

    # Check SQL ambiguous column terms (quantity, date, name, status + Arabic equivalents)
    for term in SQL_AMBIGUOUS_TERMS.keys():
        if term in query_lower:
            return "sql"

    # Check CSV ambiguous column terms (duration, time + Arabic equivalents)
    for term in CSV_AMBIGUOUS_TERMS.keys():
        if term in query_lower:
            return "csv"

    return None


router_model = ChatOllama(
    model="gpt-oss:latest",
    temperature=0,
    format="json"
)

ROUTER_PROMPT = """You are a query router for a dispatch assistant system.

Analyze the user's query and classify it with confidence level.

## Data Sources:

1. "sql" - Dispatch database:
   - Waybills, dispatch operations, deliveries, schedules
   - Contractors, vendors, routes, plants, power plants
   - Data counts, lists, statistics about dispatch operations
   - Arabic questions about the above

2. "csv" - Vehicle dwell time data:
   - How long vehicles stayed in zones/geofences
   - Zone entry/exit times, dwell time analysis
   - Driver IDs, driver analysis, zone traffic
   - Keywords: dwell, zone, geofence, stay duration

3. "pdf" - Saudi Grid Code documents:
   - Grid code regulations, policies, compliance
   - Technical procedures, specifications, standards
   - Documentation questions

4. "math" - Mathematical calculations:
   - Any arithmetic: add, subtract, multiply, divide
   - Advanced math: sqrt, power, sin, cos, log, factorial
   - Natural language math: "what is 5 plus 3", "calculate 100 divided by 4"
   - Percentages: "10 percent of 200"
   - Arabic math: حساب، جمع، طرح، ضرب، قسمة

5. "out_of_scope" - Use when:
   - Query is about general knowledge (geography, history, science)
   - Query is completely unrelated to dispatch, vehicles, grid code, or math
   - Query asks for personal opinions, jokes, or advice
   - Query is vague AND there's no conversation context to help
   - Examples: "what is the capital of Saudi Arabia", "tell me a joke"

{context}

Current Question: {query}

## Rules:
- If query clearly mentions specific keywords (waybill, dispatch, plant, dwell, zone, grid code), classify confidently
- If query is a follow-up using pronouns AND there's a previous route, use that route with "high" confidence
- If query is general knowledge or unrelated to our data sources, return "out_of_scope"
- NEVER default to "pdf" when uncertain - use "out_of_scope" instead

Respond with JSON:
{{"route": "sql"|"csv"|"pdf"|"math"|"out_of_scope", "confidence": "high"|"medium"|"low", "reason": "brief explanation"}}"""


def classify_query(query: str, session_id: str = "default") -> Dict:
    """
    Classify a query and return the route with confidence.

    Args:
        query: User's natural language query
        session_id: Session ID for conversation memory

    Returns:
        Dict with keys:
        - route: "sql", "csv", "pdf", or "out_of_scope"
        - confidence: "high", "medium", or "low"
        - reason: Brief explanation of classification
    """
    try:
        # CHECK FIRST: Detect route from column terms (e.g., "quantity" → sql, "duration" → csv)
        # This ensures queries like "give me average of the Quantity" route directly
        # to the agent, which then handles column disambiguation
        route_from_terms = detect_route_from_column_terms(query)
        if route_from_terms:
            print(f"[Router] Column term detected in query, routing to: {route_from_terms}")
            memory = SharedMemory.get_session(session_id)
            memory.set_route(route_from_terms)
            return {
                "route": route_from_terms,
                "confidence": "high",
                "reason": f"Query contains column term that maps to {route_from_terms} data source"
            }

        memory = SharedMemory.get_session(session_id)
        last_route = memory.get_route()
        messages = memory.get_messages()

        # Build context from conversation history
        user_questions = [m.content for m in messages if isinstance(m, HumanMessage)]

        context = ""
        if user_questions or last_route:
            context_parts = []
            if user_questions:
                recent = user_questions[-3:]
                context_parts.append(f"Previous questions: {recent}")
            if last_route:
                context_parts.append(f"Last route used: {last_route}")
            context = "## Conversation Context:\n" + "\n".join(context_parts)

        # Build and send prompt
        prompt = ROUTER_PROMPT.format(context=context, query=query)

        response = router_model.invoke([
            SystemMessage(content="You are a query classification assistant. Respond only with valid JSON."),
            HumanMessage(content=prompt)
        ])

        data = json.loads(response.content)
        route = data.get("route", "out_of_scope")
        confidence = data.get("confidence", "low")
        reason = data.get("reason", "")

        # Convert legacy "clarify" to "out_of_scope"
        if route == "clarify":
            route = "out_of_scope"

        print(f"[Router] Query: '{query}' -> Route: {route}, Confidence: {confidence}, Reason: {reason}")

        # Validate route
        if route not in ["sql", "csv", "pdf", "math", "out_of_scope"]:
            route = "out_of_scope"
            confidence = "low"
            reason = "Invalid route returned"

        # If it's out_of_scope but we have last_route, check if it's a follow-up
        if route == "out_of_scope" and last_route:
            # Check if reason mentions follow-up indicators
            reason_lower = reason.lower()
            if any(word in reason_lower for word in ["follow-up", "pronoun", "refer", "previous", "context", "vague"]):
                print(f"[Router] Detected follow-up context, using last route: {last_route}")
                return {
                    "route": last_route,
                    "confidence": "medium",
                    "reason": f"Detected as follow-up to previous {last_route} query"
                }

        # Build result
        result = {
            "route": route,
            "confidence": confidence,
            "reason": reason
        }

        return result

    except json.JSONDecodeError as e:
        print(f"[Router] JSON decode error: {e}")
        return {
            "route": "out_of_scope",
            "confidence": "low",
            "reason": "Could not parse router response"
        }
    except Exception as e:
        print(f"[Router] Error: {e}")
        return {
            "route": "out_of_scope",
            "confidence": "low",
            "reason": f"Router error: {str(e)}"
        }


def classify_query_simple(query: str, session_id: str = "default") -> str:
    """
    Simple wrapper that returns just the route string for backward compatibility.

    Args:
        query: User's natural language query
        session_id: Session ID for conversation memory

    Returns:
        Route string: "sql", "csv", "pdf", or "clarify"
    """
    result = classify_query(query, session_id)
    return result["route"]


def get_route_description(route: str) -> str:
    """Get a human-readable description of the route."""
    descriptions = {
        "sql": "Dispatch & Waybill Database",
        "csv": "Vehicle Dwell Time Data",
        "pdf": "Saudi Grid Code Documents",
        "math": "Math Calculator"
    }
    return descriptions.get(route, "Unknown")

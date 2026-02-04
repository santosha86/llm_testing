"""
Math Agent for handling mathematical calculations.
Uses LLM to parse natural language into math expressions and evaluates them safely.
"""

import time
import json
import math
import ast
import re
from typing import Optional, List, Any
from dataclasses import dataclass
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from ..memory import SharedMemory


# Safe functions available for math evaluation
SAFE_FUNCTIONS = {
    # Basic math
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,

    # Math module functions
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "degrees": math.degrees,
    "radians": math.radians,

    # Constants
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def add_implicit_multiplication(expr: str) -> str:
    """Add implicit multiplication operators to math expressions.

    Examples:
        3(4+5) -> 3*(4+5)
        (2+3)(4+5) -> (2+3)*(4+5)
        2(3) -> 2*(3)
    """
    # Number followed by opening parenthesis: 3( -> 3*(
    expr = re.sub(r'(\d)\(', r'\1*(', expr)
    # Closing parenthesis followed by number: )3 -> )*3
    expr = re.sub(r'\)(\d)', r')*\1', expr)
    # Closing parenthesis followed by opening parenthesis: )( -> )*(
    expr = re.sub(r'\)\(', r')*(', expr)
    return expr


def is_valid_math_expression(query: str) -> bool:
    """Check if query is already a valid math expression (not natural language)."""
    expr = query.strip()
    # Must contain at least one digit
    if not any(c.isdigit() for c in expr):
        return False
    # Must not contain letters (except e for scientific notation)
    if any(c.isalpha() and c not in 'eE' for c in expr):
        return False
    # Try to parse as Python expression (after adding implicit multiplication)
    try:
        normalized = add_implicit_multiplication(expr)
        ast.parse(normalized, mode='eval')
        return True
    except SyntaxError:
        return False


# LLM for parsing natural language to math expressions
math_model = ChatOllama(
    model="gpt-oss:latest",
    temperature=0,
    format="json"
)


MATH_PARSER_PROMPT = """You are a math expression parser. Convert the user's natural language into a Python math expression.

Available functions and constants:
- Basic: abs, round, min, max, sum, pow
- Trigonometry: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh (angles in radians)
- Logarithms: log (natural), log10, log2, exp
- Other: sqrt, floor, ceil, factorial, gcd, degrees, radians
- Constants: pi, e, tau

IMPORTANT RULES:
1. Use Python syntax: ** for power, % for modulo
2. Use function names exactly as listed above
3. For percentages: convert to decimal (e.g., "10% of 200" → "200 * 0.10")
4. For "X to the power of Y": use "X ** Y" or "pow(X, Y)"
5. Numbers in words should be converted to digits
6. Trigonometric functions expect radians by default

Examples:
- "add 5 and 3" → "5 + 3"
- "what is 5 plus 3" → "5 + 3"
- "5 times 4" → "5 * 4"
- "10 divided by 2" → "10 / 2"
- "square root of 16" → "sqrt(16)"
- "2 to the power of 8" → "2 ** 8"
- "10 percent of 200" → "200 * 0.10"
- "factorial of 5" → "factorial(5)"
- "sin of 90 degrees" → "sin(radians(90))"
- "log base 10 of 100" → "log10(100)"
- "five plus three" → "5 + 3"
- "twenty divided by four" → "20 / 4"
- "ضرب 5 في 3" → "5 * 3"
- "جمع 10 و 20" → "10 + 20"
- "الجذر التربيعي لـ 25" → "sqrt(25)"

Respond with JSON:
{"expression": "<python math expression>", "explanation": "<brief explanation in same language as query>"}

IMPORTANT: For pure math expressions (numbers and operators only), return empty explanation "".
Only provide explanation for natural language queries.

Example responses:
- Input: "add 5 and 3" → {"expression": "5 + 3", "explanation": "Adding 5 and 3"}
- Input: "what is 20% of 150" → {"expression": "150 * 0.20", "explanation": "Calculating 20 percent of 150"}
- Input: "ضرب 5 في 3" → {"expression": "5 * 3", "explanation": "ضرب 5 في 3"}
- Input: "10 + 5 * 2" → {"expression": "10 + 5 * 2", "explanation": ""}
- Input: "((10 * 48) + 5)" → {"expression": "((10 * 48) + 5)", "explanation": ""}
- Input: "10 x 5" → {"expression": "10 * 5", "explanation": ""}
- Input: "10 × 5" → {"expression": "10 * 5", "explanation": ""}
- Input: "((10 x (48 + 2) + 5 × 2) + 10)" → {"expression": "((10 * (48 + 2) + 5 * 2) + 10)", "explanation": ""}
- Input: "(5 x 3) + (2 × 4)" → {"expression": "(5 * 3) + (2 * 4)", "explanation": ""}

If the query is not a math question, return:
{"expression": null, "explanation": "This is not a math question."}"""


@dataclass
class MathAgentResponse:
    """Response from Math agent."""
    content: str
    response_time: str
    sources: List[str]
    expression: Optional[str] = None
    result: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "response_time": self.response_time,
            "sources": self.sources,
            "expression": self.expression,
            "result": self.result,
            # These fields are None for math agent but needed for consistent API
            "table_data": None,
            "sql_query": None,
            "needs_disambiguation": False,
            "disambiguation_options": None,
            "visualization": None
        }


def safe_eval(expression: str) -> Any:
    """
    Safely evaluate a math expression.
    Only allows math functions, no code execution.
    """
    # Compile the expression to check for syntax errors
    try:
        code = compile(expression, "<string>", "eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")

    # Check that only safe names are used
    for name in code.co_names:
        if name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unknown function or variable: {name}")

    # Evaluate with restricted builtins
    return eval(expression, {"__builtins__": {}}, SAFE_FUNCTIONS)


def run_math_agent(query: str, session_id: str = "default") -> MathAgentResponse:
    """
    Run Math agent on a query and return structured response.

    Args:
        query: User's natural language math query
        session_id: Session ID for conversation memory

    Returns:
        MathAgentResponse with content, expression, result, etc.
    """
    start_time = time.time()
    query_text = query.strip()

    # Get conversation memory
    memory = SharedMemory.get_session(session_id)
    memory.add_user(query_text)

    try:
        explanation = None  # Will be set by LLM for natural language queries

        # Check if input is already a valid math expression
        if is_valid_math_expression(query_text):
            # Convert ^ to ** for Python power operator and add implicit multiplication
            expression = add_implicit_multiplication(query_text.replace('^', '**'))
        else:
            # Use LLM to parse natural language to math expression
            system_msg = SystemMessage(content=MATH_PARSER_PROMPT)
            human_msg = HumanMessage(content=query_text)

            response = math_model.invoke([system_msg, human_msg])
            data = json.loads(response.content)

            expression = data.get("expression")
            explanation = data.get("explanation")

        elapsed_time = round(time.time() - start_time, 2)

        # Check if it's not a math question (only possible from LLM path)
        if expression is None:
            result_response = MathAgentResponse(
                content="I couldn't parse this as a math question. Please try rephrasing.",
                response_time=f"{elapsed_time}s",
                sources=["Math Calculator"]
            )
            memory.add_ai(result_response.content)
            return result_response

        # Evaluate the expression safely
        try:
            result = safe_eval(expression)

            # Format the result nicely
            if isinstance(result, float):
                # Round to reasonable precision
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 10)

            # Generate natural language response - show original query
            # Wrap in backticks to prevent ReactMarkdown from interpreting * as formatting
            content = f"`{query_text}` = **{result}**"

            # Add explanation if available (from LLM for natural language queries)
            if explanation:
                content += f"\n\n_{explanation}_"

            result_response = MathAgentResponse(
                content=content,
                response_time=f"{elapsed_time}s",
                sources=["Math Calculator"],
                expression=expression,
                result=result
            )
            memory.add_ai(result_response.content)
            return result_response

        except ValueError as e:
            result_response = MathAgentResponse(
                content=f"**Error evaluating expression:** `{expression}`\n\n{str(e)}",
                response_time=f"{elapsed_time}s",
                sources=["Math Calculator"],
                expression=expression
            )
            memory.add_ai(result_response.content)
            return result_response

        except Exception as e:
            result_response = MathAgentResponse(
                content=f"**Calculation error:** {str(e)}\n\nExpression: `{expression}`",
                response_time=f"{elapsed_time}s",
                sources=["Math Calculator"],
                expression=expression
            )
            memory.add_ai(result_response.content)
            return result_response

    except json.JSONDecodeError as e:
        elapsed_time = round(time.time() - start_time, 2)
        result_response = MathAgentResponse(
            content=f"**Error:** Failed to parse LLM response.\n\n{str(e)}",
            response_time=f"{elapsed_time}s",
            sources=["Math Calculator"]
        )
        memory.add_ai(result_response.content)
        return result_response

    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        result_response = MathAgentResponse(
            content=f"**Error:** {str(e)}",
            response_time=f"{elapsed_time}s",
            sources=["Math Calculator"]
        )
        memory.add_ai(result_response.content)
        return result_response

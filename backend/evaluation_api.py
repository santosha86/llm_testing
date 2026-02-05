"""
LLM Evaluation API endpoints for running batch tests
"""
import os
import sys
import time
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class ProviderType(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"


class ProviderConfig(BaseModel):
    type: ProviderType
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None
    model: str


class EvaluationRequest(BaseModel):
    baseline: ProviderConfig
    target: ProviderConfig
    useCachedTarget: Optional[bool] = False


class TestResult(BaseModel):
    testId: str
    category: str
    question: str
    expected: str
    baselineAnswer: Optional[str] = None
    targetAnswer: Optional[str] = None
    baselinePass: Optional[bool] = None
    targetPass: Optional[bool] = None
    baselineLatency: Optional[float] = None
    targetLatency: Optional[float] = None


class EvaluationResponse(BaseModel):
    status: str
    category: str
    results: List[TestResult]
    summary: Dict[str, Any]


# Test definitions by category
MATH_TESTS = [
    {"testId": "MATH-001", "question": "Calculate annual energy for Sakaka Solar (300 MW, 24% CF)", "expected": "630,720 MWh"},
    {"testId": "MATH-002", "question": "Calculate revenue for project with 0.0877 SAR/kWh tariff and 630,720 MWh", "expected": "55,296,144 SAR"},
    {"testId": "MATH-003", "question": "Sum total capacity of all operational projects in the portfolio", "expected": "1,550 MW"},
    {"testId": "MATH-004", "question": "Calculate average capacity factor across all wind projects", "expected": "42%"},
    {"testId": "MATH-005", "question": "What is the lowest tariff among solar projects?", "expected": "0.0104 SAR/kWh"},
    {"testId": "MATH-006", "question": "Calculate total Round 7 budget (equipment + construction + grid + soft costs)", "expected": "12.5 billion SAR"},
]

LOGIC_TESTS = [
    {"testId": "LOGIC-001", "question": "Is a bidder with 30% local content eligible for Round 7?", "expected": "No (minimum 35%)"},
    {"testId": "LOGIC-002", "question": "Can Northern Region support 900 MW new capacity given 1400 MW available?", "expected": "Yes"},
    {"testId": "LOGIC-003", "question": "Which technology is required for solar PV projects in Round 7?", "expected": "Bifacial modules with single-axis tracking"},
    {"testId": "LOGIC-004", "question": "If expected tariff range is 0.85-1.05 SAR/kWh, would a 1.20 SAR/kWh bid be competitive?", "expected": "No"},
    {"testId": "LOGIC-005", "question": "Is fixed-rate financing required in the PPA according to risk mitigation measures?", "expected": "Yes"},
    {"testId": "LOGIC-006", "question": "What is the minimum module efficiency requirement for Round 7?", "expected": "21%"},
]

RETRIEVAL_TESTS = [
    {"testId": "RET-001", "question": "What is the RFQ issuance date for Round 7?", "expected": "January 15, 2025"},
    {"testId": "RET-002", "question": "What is the expected winning tariff range mentioned in internal notes?", "expected": "0.85 - 1.05 SAR/kWh"},
    {"testId": "RET-003", "question": "What is the total Round 7 capacity target?", "expected": "2,500 MW"},
    {"testId": "RET-004", "question": "When is PPA signing expected according to the key dates?", "expected": "December 2025"},
    {"testId": "RET-005", "question": "What is the equipment budget for Round 7?", "expected": "SAR 8.0 billion"},
    {"testId": "RET-006", "question": "List all regions with planned capacity in Round 7", "expected": "Northern, Central, Eastern, Western"},
]

# Store for running evaluations
evaluation_runs: Dict[str, Dict] = {}


def get_llm_for_config(config: ProviderConfig):
    """Create LLM instance based on provider config"""
    if config.type == ProviderType.OPENAI:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            api_key=config.apiKey,
            temperature=0
        )
    elif config.type == ProviderType.OLLAMA:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=config.model,
            base_url=config.baseUrl or "http://localhost:11434",
            temperature=0
        )
    else:
        raise ValueError(f"Unknown provider type: {config.type}")


def run_single_test(llm, test: Dict, data_context: str) -> Dict:
    """Run a single test against an LLM"""
    from langchain_core.messages import HumanMessage, SystemMessage

    prompt = f"""You are an expert analyst. Answer the following question based on the provided data.
Be precise and provide exact numbers when asked for calculations.

DATA:
{data_context}

QUESTION: {test['question']}

Provide a concise answer. If it's a calculation, show the result directly.
"""

    start_time = time.time()
    try:
        response = llm.invoke([
            SystemMessage(content="You are a precise analytical assistant. Give exact answers."),
            HumanMessage(content=prompt)
        ])
        answer = response.content.strip()
        latency = (time.time() - start_time) * 1000  # ms

        # Simple pass/fail check - does the answer contain the expected value?
        expected = test['expected'].lower()
        answer_lower = answer.lower()

        # Extract key numbers/values from expected
        passed = any(part in answer_lower for part in expected.split() if len(part) > 2)

        return {
            "answer": answer,
            "latency": latency,
            "passed": passed
        }
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "latency": (time.time() - start_time) * 1000,
            "passed": False
        }


def load_test_data():
    """Load test data from files"""
    test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_framework", "test_data")

    data_context = ""

    # Load CSV data
    csv_path = os.path.join(test_data_dir, "sppc_project_portfolio.csv")
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            data_context += "PROJECT PORTFOLIO DATA:\n" + f.read() + "\n\n"

    # Load Round 7 summary
    md_path = os.path.join(test_data_dir, "sppc_round7_summary.md")
    if os.path.exists(md_path):
        with open(md_path, 'r') as f:
            data_context += "ROUND 7 PLANNING DOCUMENT:\n" + f.read() + "\n\n"

    # Load eligibility rules
    rules_path = os.path.join(test_data_dir, "bidder_eligibility_rules.md")
    if os.path.exists(rules_path):
        with open(rules_path, 'r') as f:
            data_context += "BIDDER ELIGIBILITY RULES:\n" + f.read() + "\n\n"

    return data_context


@router.post("/test-connection")
async def test_connection(config: ProviderConfig):
    """Test connection to an LLM provider"""
    try:
        llm = get_llm_for_config(config)
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'OK' if you can hear me.")])
        return {"status": "success", "message": "Connection successful", "response": response.content[:100]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/run/{category}", response_model=EvaluationResponse)
async def run_evaluation(category: str, request: EvaluationRequest):
    """Run evaluation for a specific category"""

    # Select tests based on category
    tests = {
        "math": MATH_TESTS,
        "logic": LOGIC_TESTS,
        "retrieval": RETRIEVAL_TESTS
    }.get(category.lower(), [])

    if not tests:
        return EvaluationResponse(
            status="error",
            category=category,
            results=[],
            summary={"error": f"Unknown category: {category}"}
        )

    # Load test data
    data_context = load_test_data()

    # Cache file path
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    target_model_id = f"{request.target.type}_{request.target.model}".replace(":", "_").replace("/", "_")
    cache_file = os.path.join(cache_dir, f"{category}_{target_model_id}.json")

    # Load cached target results if requested
    cached_target_results = {}
    if request.useCachedTarget and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                cached_target_results = {r["testId"]: r for r in cache_data}
        except:
            pass  # Ignore cache errors

    # Create LLM instances
    try:
        baseline_llm = get_llm_for_config(request.baseline)
        # Only create target LLM if we need to run it
        target_llm = None if (request.useCachedTarget and cached_target_results) else get_llm_for_config(request.target)
    except Exception as e:
        return EvaluationResponse(
            status="error",
            category=category,
            results=[],
            summary={"error": f"Failed to initialize LLM: {str(e)}"}
        )

    results = []
    baseline_passed = 0
    target_passed = 0
    target_results_for_cache = []

    for test in tests:
        # Always run baseline fresh
        baseline_result = run_single_test(baseline_llm, test, data_context)

        # Use cached or run target
        if request.useCachedTarget and test["testId"] in cached_target_results:
            # Use cached result
            cached = cached_target_results[test["testId"]]
            target_result = {
                "answer": cached["answer"],
                "latency": cached["latency"],
                "passed": cached["passed"]
            }
        else:
            # Run target
            target_result = run_single_test(target_llm, test, data_context)
            # Save for cache
            target_results_for_cache.append({
                "testId": test["testId"],
                "answer": target_result["answer"],
                "latency": target_result["latency"],
                "passed": target_result["passed"]
            })

        if baseline_result["passed"]:
            baseline_passed += 1
        if target_result["passed"]:
            target_passed += 1

        results.append(TestResult(
            testId=test["testId"],
            category=category,
            question=test["question"],
            expected=test["expected"],
            baselineAnswer=baseline_result["answer"],
            targetAnswer=target_result["answer"],
            baselinePass=baseline_result["passed"],
            targetPass=target_result["passed"],
            baselineLatency=baseline_result["latency"],
            targetLatency=target_result["latency"]
        ))

    # Save target results to cache if we ran them
    if target_results_for_cache:
        try:
            with open(cache_file, 'w') as f:
                json.dump(target_results_for_cache, f)
        except:
            pass  # Ignore cache write errors

    total = len(tests)
    summary = {
        "total": total,
        "baselinePassed": baseline_passed,
        "targetPassed": target_passed,
        "baselineRate": round(baseline_passed / total * 100),
        "targetRate": round(target_passed / total * 100),
        "gap": round((baseline_passed - target_passed) / total * 100)
    }

    return EvaluationResponse(
        status="completed",
        category=category,
        results=results,
        summary=summary
    )


@router.get("/categories")
async def get_categories():
    """Get available test categories"""
    return {
        "categories": [
            {"id": "math", "name": "Math Tests", "count": len(MATH_TESTS)},
            {"id": "logic", "name": "Logic Tests", "count": len(LOGIC_TESTS)},
            {"id": "retrieval", "name": "Retrieval Tests", "count": len(RETRIEVAL_TESTS)}
        ]
    }


@router.get("/tests/{category}")
async def get_tests(category: str):
    """Get tests for a specific category"""
    tests = {
        "math": MATH_TESTS,
        "logic": LOGIC_TESTS,
        "retrieval": RETRIEVAL_TESTS
    }.get(category.lower(), [])

    return {"category": category, "tests": tests}

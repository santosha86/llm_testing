"""
Logic Reasoning Agent for Multi-Condition Evaluation

This agent handles complex rule-based reasoning:
- Multiple eligibility criteria evaluation
- AND/OR condition handling
- What-if scenario analysis
- Ranking with multiple criteria

Designed to expose LLM capability differences between providers.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm_provider import get_llm, LLMProvider
from langchain_core.messages import SystemMessage, HumanMessage


class StepStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """Represents a single step in the reasoning process"""
    step_number: int
    action: str
    expected_behavior: str
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0


@dataclass
class LogicResult:
    """Result of a logic reasoning task"""
    success: bool
    final_answer: Any
    steps: List[ExecutionStep] = field(default_factory=list)
    total_latency_ms: float = 0
    provider: str = ""
    raw_llm_response: str = ""


LOGIC_SYSTEM_PROMPT = """You are an expert eligibility analyst. You must evaluate bidders against a set of rules.

## ELIGIBILITY RULES (ALL must be met):

### Rule 1: Local Content Requirement
- Minimum local content percentage: **30%**

### Rule 2: Financial Rating
- Minimum credit rating: **BBB** (or equivalent)
- Rating hierarchy: AAA > AA+ > AA > AA- > A+ > A > A- > BBB+ > BBB > BBB- > BB+ > BB > BB- > ...

### Rule 3: Track Record
- Minimum completed renewable energy projects: **3 projects**

### Rule 4: Technical Capacity
- Minimum installed capacity experience: **100 MW**

### Rule 5: Safety Record
- Maximum lost time injury rate (LTIR): **0.5**

## ADDITIONAL RULE:
- If proposed tariff is below **1.00 SAR/kWh**, bidder requires additional performance bond

## BIDDER DATA:

| Bidder | Local Content % | Credit Rating | Completed Projects | Total MW | LTIR | Proposed Tariff |
|--------|----------------|---------------|-------------------|----------|------|-----------------|
| Bidder A | 35% | A+ | 5 | 450 MW | 0.3 | 1.20 SAR/kWh |
| Bidder B | 42% | BBB | 4 | 320 MW | 0.4 | 0.95 SAR/kWh |
| Bidder C | 28% | AA | 6 | 580 MW | 0.2 | 1.15 SAR/kWh |
| Bidder D | 25% | BB | 2 | 150 MW | 0.6 | 1.10 SAR/kWh |
| Bidder E | 38% | BBB+ | 3 | 200 MW | 0.4 | 0.88 SAR/kWh |

## YOUR TASK:
Analyze the query and provide a structured response.

## RESPONSE FORMAT (JSON only):
{{
    "reasoning": "Step-by-step analysis of each rule for each relevant bidder",
    "evaluation_details": [
        {{
            "bidder": "Bidder X",
            "rule_results": {{
                "rule_1_local_content": {{"pass": true/false, "value": "X%", "required": "30%"}},
                "rule_2_credit_rating": {{"pass": true/false, "value": "X", "required": "BBB"}},
                "rule_3_track_record": {{"pass": true/false, "value": X, "required": 3}},
                "rule_4_capacity": {{"pass": true/false, "value": "X MW", "required": "100 MW"}},
                "rule_5_safety": {{"pass": true/false, "value": X, "required": "≤0.5"}}
            }},
            "eligible": true/false,
            "disqualification_reasons": ["reason1", "reason2"] or [],
            "requires_bond": true/false
        }}
    ],
    "final_answer": "Summary answer to the specific question",
    "confidence": "high" or "medium" or "low"
}}
"""


class LogicAgent:
    """Agent for multi-condition logic reasoning"""

    def __init__(self, provider: LLMProvider = None):
        """
        Initialize the logic agent.

        Args:
            provider: LLM provider to use (defaults to env setting)
        """
        self.provider = provider
        self.llm = get_llm(provider=provider, json_mode=True)

    def execute(self, query: str) -> LogicResult:
        """
        Execute a logic reasoning query.

        Args:
            query: Natural language query about eligibility/rules

        Returns:
            LogicResult with steps and final answer
        """
        start_time = time.time()
        steps = []

        # Step 1: Parse query
        step1 = ExecutionStep(
            step_number=1,
            action="Parse query and identify task",
            expected_behavior="Understand what evaluation is being requested"
        )
        step1.status = StepStatus.SUCCESS
        step1.result = f"Query: {query[:100]}..."
        step1.latency_ms = 0
        steps.append(step1)

        # Step 2: LLM reasoning
        step2_start = time.time()
        step2 = ExecutionStep(
            step_number=2,
            action="Apply rules and evaluate conditions",
            expected_behavior="LLM evaluates each bidder against all rules"
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content=LOGIC_SYSTEM_PROMPT),
                HumanMessage(content=query)
            ])

            raw_response = response.content
            step2.latency_ms = (time.time() - step2_start) * 1000

            # Parse JSON response
            try:
                result_data = json.loads(raw_response)
                step2.status = StepStatus.SUCCESS
                step2.result = result_data
            except json.JSONDecodeError as e:
                step2.status = StepStatus.FAILED
                step2.error = f"Invalid JSON response: {str(e)}"
                step2.result = raw_response
                steps.append(step2)
                return LogicResult(
                    success=False,
                    final_answer=None,
                    steps=steps,
                    total_latency_ms=(time.time() - start_time) * 1000,
                    provider=self.provider.value if self.provider else "default",
                    raw_llm_response=raw_response
                )

        except Exception as e:
            step2.status = StepStatus.FAILED
            step2.error = str(e)
            step2.latency_ms = (time.time() - step2_start) * 1000
            steps.append(step2)
            return LogicResult(
                success=False,
                final_answer=None,
                steps=steps,
                total_latency_ms=(time.time() - start_time) * 1000,
                provider=self.provider.value if self.provider else "default"
            )

        steps.append(step2)

        # Step 3: Validate completeness
        step3 = ExecutionStep(
            step_number=3,
            action="Validate response completeness",
            expected_behavior="Check all required fields are present"
        )

        final_answer = result_data.get("final_answer")
        has_evaluation = "evaluation_details" in result_data or "reasoning" in result_data

        if final_answer and has_evaluation:
            step3.status = StepStatus.SUCCESS
            step3.result = "Response complete with evaluation details"
        else:
            step3.status = StepStatus.FAILED
            step3.error = "Missing final_answer or evaluation_details"

        step3.latency_ms = 0
        steps.append(step3)

        total_latency = (time.time() - start_time) * 1000

        return LogicResult(
            success=step3.status == StepStatus.SUCCESS,
            final_answer=result_data,
            steps=steps,
            total_latency_ms=total_latency,
            provider=self.provider.value if self.provider else "default",
            raw_llm_response=raw_response
        )

    def identify_eligible_bidders(self) -> LogicResult:
        """Identify which bidders are eligible"""
        query = """Which bidders are ELIGIBLE based on all 5 rules?

        For each bidder, check ALL rules and determine if they pass or fail.
        A bidder is eligible ONLY if they pass ALL 5 rules."""

        return self.execute(query)

    def identify_disqualified_with_reasons(self) -> LogicResult:
        """Identify disqualified bidders with specific reasons"""
        query = """Which bidders are DISQUALIFIED and why?

        For each disqualified bidder:
        1. List ALL rules they failed (not just one)
        2. Show the actual value vs required value
        3. Be specific about each failure"""

        return self.execute(query)

    def check_multiple_failures(self) -> LogicResult:
        """Check if any bidder fails multiple rules (tests AND logic)"""
        query = """Is there any bidder who fails MORE THAN ONE rule?

        If yes, identify:
        1. Which bidder(s)
        2. EXACTLY which rules they fail
        3. The specific values that caused each failure

        This is important - I need to know ALL failures for each bidder, not just the first one found."""

        return self.execute(query)

    def identify_bond_requirements(self) -> LogicResult:
        """Identify which eligible bidders require performance bond"""
        query = """Among the ELIGIBLE bidders, which ones require an additional performance bond?

        Remember: Performance bond is required if proposed tariff < 1.00 SAR/kWh

        List the eligible bidders who need a bond and their proposed tariffs."""

        return self.execute(query)

    def what_if_relax_rule(self, rule_to_relax: str = "local content") -> LogicResult:
        """What-if analysis: how does eligibility change if we relax one rule"""
        query = f"""WHAT-IF ANALYSIS:

        If we REMOVE the {rule_to_relax} requirement (Rule 1), which previously DISQUALIFIED bidders would now become ELIGIBLE?

        Show your analysis:
        1. List currently disqualified bidders
        2. Check if they pass ALL OTHER rules (Rules 2-5)
        3. Identify who becomes eligible after relaxing the rule"""

        return self.execute(query)

    def rank_eligible_bidders(self) -> LogicResult:
        """Rank eligible bidders by tariff (lower is better)"""
        query = """Rank the ELIGIBLE bidders by their proposed tariff from lowest (best) to highest.

        Only include bidders who pass ALL 5 eligibility rules.

        Format:
        1. Bidder X - Y SAR/kWh (lowest tariff = best)
        2. Bidder Y - Z SAR/kWh
        ..."""

        return self.execute(query)


def run_logic_tests(provider: LLMProvider) -> Dict[str, LogicResult]:
    """
    Run all logic reasoning tests for a given provider.

    Args:
        provider: LLM provider to test

    Returns:
        Dictionary of test name -> LogicResult
    """
    agent = LogicAgent(provider=provider)

    results = {}

    # Test 2.1: Identify eligible bidders
    print(f"  Running Test 2.1: Identify eligible bidders...")
    results["2.1_eligible"] = agent.identify_eligible_bidders()

    # Test 2.2: Identify disqualified with reasons
    print(f"  Running Test 2.2: Disqualified bidders with reasons...")
    results["2.2_disqualified"] = agent.identify_disqualified_with_reasons()

    # Test 2.3: Check multiple failures (AND logic)
    print(f"  Running Test 2.3: Multiple rule failures (AND logic)...")
    results["2.3_multiple_failures"] = agent.check_multiple_failures()

    # Test 2.4: Bond requirements
    print(f"  Running Test 2.4: Performance bond requirements...")
    results["2.4_bond_required"] = agent.identify_bond_requirements()

    # Test 2.5: What-if analysis
    print(f"  Running Test 2.5: What-if rule relaxation...")
    results["2.5_what_if"] = agent.what_if_relax_rule()

    # Test 2.6: Rank eligible bidders
    print(f"  Running Test 2.6: Rank eligible bidders...")
    results["2.6_ranking"] = agent.rank_eligible_bidders()

    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("Testing Logic Agent...")
    print("-" * 50)

    try:
        results = run_logic_tests(LLMProvider.OPENAI)
        for test_name, result in results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{test_name}: {status} ({result.total_latency_ms:.0f}ms)")
    except Exception as e:
        print(f"Error: {e}")

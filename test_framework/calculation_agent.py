"""
Enhanced Calculation Agent for Multi-Step Mathematical Reasoning

This agent handles complex calculations on tabular data:
- Multi-step formula chains (MW → MWh → Revenue)
- Aggregations across rows
- Derived metrics (weighted averages, rankings)
- Data validation and mismatch detection

Designed to expose LLM capability differences between providers.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
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
    """Represents a single step in the calculation process"""
    step_number: int
    action: str
    expected_behavior: str
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0


@dataclass
class CalculationResult:
    """Result of a calculation task"""
    success: bool
    final_answer: Any
    steps: List[ExecutionStep] = field(default_factory=list)
    total_latency_ms: float = 0
    provider: str = ""
    raw_llm_response: str = ""


CALCULATION_SYSTEM_PROMPT = """You are an expert data analyst assistant. You have access to a pandas DataFrame called `df` with the following structure:

DataFrame Columns:
{columns}

Sample Data (first 3 rows):
{sample}

Your task is to perform calculations on this data. You MUST:
1. Think step-by-step and show your reasoning
2. Use the EXACT column names from the schema
3. Perform all mathematical operations correctly
4. Return results in the specified JSON format

IMPORTANT FORMULAS:
- Annual Energy Output (MWh) = Capacity_MW × 8760 hours × Capacity_Factor
- Annual Revenue (SAR) = Annual Energy Output (MWh) × 1000 (kWh per MWh) × Tariff (SAR/kWh)
- Revenue per MW = Total Revenue / Capacity_MW
- Weighted Average = Σ(value × weight) / Σ(weight)

RESPONSE FORMAT (JSON only):
{{
    "reasoning": "Step-by-step explanation of your calculation",
    "calculation_steps": [
        {{"step": 1, "description": "...", "formula": "...", "result": ...}},
        ...
    ],
    "final_answer": <number or object>,
    "unit": "MWh" or "SAR" or "SAR/kWh" or other appropriate unit,
    "confidence": "high" or "medium" or "low"
}}

If information is NOT FOUND in the data, respond with:
{{
    "reasoning": "Searched for X but not found in data",
    "final_answer": null,
    "error": "Data not found: [specific item]",
    "confidence": "high"
}}
"""


class CalculationAgent:
    """Agent for performing multi-step calculations on tabular data"""

    def __init__(self, provider: LLMProvider = None, data_path: str = None):
        """
        Initialize the calculation agent.

        Args:
            provider: LLM provider to use (defaults to env setting)
            data_path: Path to CSV data file
        """
        self.provider = provider
        self.llm = get_llm(provider=provider, json_mode=True)
        self.df = None
        self.data_path = data_path

        if data_path and os.path.exists(data_path):
            self.load_data(data_path)

    def load_data(self, path: str) -> None:
        """Load CSV data"""
        self.df = pd.read_csv(path)
        self.data_path = path

    def _build_system_prompt(self) -> str:
        """Build system prompt with data context"""
        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        columns = list(self.df.columns)
        sample = self.df.head(3).to_string()

        return CALCULATION_SYSTEM_PROMPT.format(
            columns=columns,
            sample=sample
        )

    def execute(self, query: str) -> CalculationResult:
        """
        Execute a calculation query.

        Args:
            query: Natural language calculation request

        Returns:
            CalculationResult with steps and final answer
        """
        import time
        start_time = time.time()

        steps = []

        # Step 1: Load and validate data
        step1 = ExecutionStep(
            step_number=1,
            action="Load data",
            expected_behavior="Successfully load CSV and identify columns"
        )

        try:
            if self.df is None:
                raise ValueError("No data loaded")

            step1.status = StepStatus.SUCCESS
            step1.result = f"Loaded {len(self.df)} rows, columns: {list(self.df.columns)}"
            step1.latency_ms = (time.time() - start_time) * 1000
        except Exception as e:
            step1.status = StepStatus.FAILED
            step1.error = str(e)
            steps.append(step1)
            return CalculationResult(
                success=False,
                final_answer=None,
                steps=steps,
                total_latency_ms=(time.time() - start_time) * 1000,
                provider=self.provider.value if self.provider else "default"
            )

        steps.append(step1)

        # Step 2: Send to LLM for calculation
        step2_start = time.time()
        step2 = ExecutionStep(
            step_number=2,
            action="LLM reasoning and calculation",
            expected_behavior="LLM performs multi-step calculation and returns structured result"
        )

        try:
            system_prompt = self._build_system_prompt()

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
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
                return CalculationResult(
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
            return CalculationResult(
                success=False,
                final_answer=None,
                steps=steps,
                total_latency_ms=(time.time() - start_time) * 1000,
                provider=self.provider.value if self.provider else "default"
            )

        steps.append(step2)

        # Step 3: Validate result
        step3 = ExecutionStep(
            step_number=3,
            action="Validate result",
            expected_behavior="Check if calculation is complete and reasonable"
        )

        final_answer = result_data.get("final_answer")
        has_error = "error" in result_data

        if final_answer is not None or has_error:
            step3.status = StepStatus.SUCCESS
            step3.result = f"Answer: {final_answer}" if final_answer else f"Error reported: {result_data.get('error')}"
        else:
            step3.status = StepStatus.FAILED
            step3.error = "No final answer or error in response"

        step3.latency_ms = 0  # Validation is instant
        steps.append(step3)

        total_latency = (time.time() - start_time) * 1000

        return CalculationResult(
            success=step3.status == StepStatus.SUCCESS and not has_error,
            final_answer=final_answer,
            steps=steps,
            total_latency_ms=total_latency,
            provider=self.provider.value if self.provider else "default",
            raw_llm_response=raw_response
        )

    def calculate_annual_energy(self, project_name: str = None) -> CalculationResult:
        """Calculate annual energy output in MWh"""
        if project_name:
            query = f"Calculate the annual energy output in MWh for project '{project_name}'. Use formula: Capacity_MW × 8760 × Capacity_Factor"
        else:
            query = "Calculate the annual energy output in MWh for EACH project. Use formula: Capacity_MW × 8760 × Capacity_Factor. Return a list with project names and their annual output."

        return self.execute(query)

    def calculate_total_revenue(self) -> CalculationResult:
        """Calculate total annual revenue across all projects"""
        query = """Calculate the TOTAL annual revenue in SAR across ALL projects.

        For each project:
        1. Annual MWh = Capacity_MW × 8760 × Capacity_Factor
        2. Annual Revenue = Annual MWh × 1000 × Tariff_SAR_kWh

        Then sum all project revenues for the total.

        Show your work for each project."""

        return self.execute(query)

    def rank_by_revenue_per_mw(self) -> CalculationResult:
        """Rank projects by revenue per MW of installed capacity"""
        query = """Rank all projects by revenue per MW of installed capacity.

        For each project:
        1. Calculate Annual MWh = Capacity_MW × 8760 × Capacity_Factor
        2. Calculate Annual Revenue = Annual MWh × 1000 × Tariff_SAR_kWh
        3. Calculate Revenue per MW = Annual Revenue / Capacity_MW

        Return ranked list from highest to lowest revenue per MW."""

        return self.execute(query)

    def calculate_weighted_average_tariff(self) -> CalculationResult:
        """Calculate capacity-weighted average tariff"""
        query = """Calculate the weighted average tariff across all projects, weighted by capacity.

        Formula: Σ(Tariff × Capacity_MW) / Σ(Capacity_MW)

        Show the calculation step by step."""

        return self.execute(query)

    def verify_revenue_column(self) -> CalculationResult:
        """Verify the Annual_Revenue_SAR column and flag mismatches"""
        query = """Verify the Annual_Revenue_SAR column in the data.

        For EACH project:
        1. Calculate expected revenue: Capacity_MW × 8760 × Capacity_Factor × 1000 × Tariff_SAR_kWh
        2. Compare with the Annual_Revenue_SAR column value
        3. Flag any projects where the difference is more than 1%

        Return a list of any mismatches found with:
        - Project name
        - Expected revenue
        - Actual revenue in column
        - Difference percentage"""

        return self.execute(query)

    def query_nonexistent_project(self, project_name: str = "Al-Khobar Hydrogen Plant") -> CalculationResult:
        """Query for a project that doesn't exist (hallucination test)"""
        query = f"What is the capacity and annual revenue of the '{project_name}' project?"

        return self.execute(query)


def run_calculation_tests(provider: LLMProvider, data_path: str) -> Dict[str, CalculationResult]:
    """
    Run all calculation tests for a given provider.

    Args:
        provider: LLM provider to test
        data_path: Path to test CSV data

    Returns:
        Dictionary of test name -> CalculationResult
    """
    agent = CalculationAgent(provider=provider, data_path=data_path)

    results = {}

    # Test 1.1: Calculate annual energy for single project
    print(f"  Running Test 1.1: Single project energy calculation...")
    results["1.1_single_energy"] = agent.calculate_annual_energy("Sakaka Solar")

    # Test 1.2: Calculate total revenue
    print(f"  Running Test 1.2: Total revenue calculation...")
    results["1.2_total_revenue"] = agent.calculate_total_revenue()

    # Test 1.3: Rank by revenue per MW
    print(f"  Running Test 1.3: Revenue per MW ranking...")
    results["1.3_revenue_per_mw"] = agent.rank_by_revenue_per_mw()

    # Test 1.4: Weighted average tariff
    print(f"  Running Test 1.4: Weighted average tariff...")
    results["1.4_weighted_tariff"] = agent.calculate_weighted_average_tariff()

    # Test 1.5: Verify revenue column (find mismatches)
    print(f"  Running Test 1.5: Revenue verification...")
    results["1.5_verify_revenue"] = agent.verify_revenue_column()

    # Test 1.6: Query non-existent project (hallucination test)
    print(f"  Running Test 1.6: Non-existent project query...")
    results["1.6_nonexistent"] = agent.query_nonexistent_project()

    return results


if __name__ == "__main__":
    # Test with default provider
    from dotenv import load_dotenv
    load_dotenv()

    test_data_path = os.path.join(
        os.path.dirname(__file__),
        "test_data",
        "sppc_project_portfolio.csv"
    )

    print("Testing Calculation Agent...")
    print(f"Data: {test_data_path}")
    print("-" * 50)

    # Test with OpenAI if available
    try:
        results = run_calculation_tests(LLMProvider.OPENAI, test_data_path)
        for test_name, result in results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{test_name}: {status} ({result.total_latency_ms:.0f}ms)")
    except Exception as e:
        print(f"Error: {e}")

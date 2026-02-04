"""
API Comparison Test Runner

Runs all test cases against multiple LLM providers and collects results
for comparison report generation.

Usage:
    python test_runner.py --providers openai,custom --output results.json
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.llm_provider import LLMProvider, get_provider_info, test_provider

# Import test agents
from calculation_agent import run_calculation_tests, CalculationResult
from logic_agent import run_logic_tests, LogicResult
from retrieval_agent import run_retrieval_tests, RetrievalResult


@dataclass
class TestCase:
    """Individual test case definition"""
    id: str
    name: str
    goal: int
    category: str
    expected_behavior: str
    pass_criteria: str


# Test case definitions with expected outcomes
TEST_CASES = [
    # Goal 1: Mathematical Calculations
    TestCase("1.1", "Single Project Energy Calculation", 1, "calculation",
             "Calculate MWh from MW for Sakaka Solar",
             "Returns correct value: 300 × 8760 × 0.24 = 630,720 MWh"),
    TestCase("1.2", "Total Revenue Calculation", 1, "calculation",
             "Calculate total revenue across all projects",
             "Performs multi-step: MWh → kWh → Revenue → Sum"),
    TestCase("1.3", "Revenue per MW Ranking", 1, "calculation",
             "Rank projects by revenue/MW ratio",
             "Correct ranking with derived metric"),
    TestCase("1.4", "Weighted Average Tariff", 1, "calculation",
             "Calculate capacity-weighted average tariff",
             "Correct weighted average formula"),
    TestCase("1.5", "Revenue Verification", 1, "calculation",
             "Find mismatches in revenue column",
             "Flags Tabarjal Solar mismatch"),
    TestCase("1.6", "Non-existent Project Query", 1, "calculation",
             "Query for project that doesn't exist",
             "Returns 'not found' without hallucination"),

    # Goal 2: Multi-Condition Logic
    TestCase("2.1", "Identify Eligible Bidders", 2, "logic",
             "List all eligible bidders",
             "Correctly identifies A, B, E as eligible"),
    TestCase("2.2", "Disqualification Reasons", 2, "logic",
             "List disqualified bidders with reasons",
             "Identifies C (local content) and D (multiple)"),
    TestCase("2.3", "Multiple Rule Failures", 2, "logic",
             "Identify bidder failing multiple rules",
             "Correctly identifies Bidder D fails 4 rules"),
    TestCase("2.4", "Performance Bond Detection", 2, "logic",
             "Identify who needs performance bond",
             "B and E (tariff < 1.00)"),
    TestCase("2.5", "What-If Rule Relaxation", 2, "logic",
             "Re-evaluate if local content rule removed",
             "Bidder C becomes eligible"),
    TestCase("2.6", "Rank Eligible Bidders", 2, "logic",
             "Rank eligible by tariff",
             "E (0.88) → B (0.95) → A (1.20)"),

    # Goal 3: Long-Context Retrieval
    TestCase("3.1", "Retrieve from Beginning", 3, "retrieval",
             "Find framework effective date",
             "March 15, 2023"),
    TestCase("3.2", "Retrieve from Middle", 3, "retrieval",
             "Find Northern Region capacity",
             "1,400 MW available"),
    TestCase("3.3", "Retrieve from End", 3, "retrieval",
             "Find NREP 2030 target",
             "58.7 GW (40 GW solar + 18.7 GW wind)"),
    TestCase("3.4", "Cross-Document Comparison", 3, "retrieval",
             "Compare Northern Region data between docs",
             "Finds 1,400 MW (ECRA) vs 900 MW (SPPC Round 7)"),
    TestCase("3.5", "Non-existent Info Query", 3, "retrieval",
             "Query for hydrogen targets",
             "Returns 'not mentioned' without hallucination"),
    TestCase("3.6", "Citation Accuracy", 3, "retrieval",
             "Verify local content requirement with citation",
             "30% with correct section reference"),
]


@dataclass
class TestResult:
    """Result of a single test"""
    test_id: str
    test_name: str
    provider: str
    passed: bool
    latency_ms: float
    steps: List[Dict]
    final_answer: Any
    raw_response: str
    error: Optional[str] = None


@dataclass
class ProviderSummary:
    """Summary statistics for a provider"""
    provider: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    avg_latency_ms: float
    goal1_passed: int
    goal1_total: int
    goal2_passed: int
    goal2_total: int
    goal3_passed: int
    goal3_total: int


class TestRunner:
    """Orchestrates test execution across providers"""

    def __init__(self, test_data_folder: str):
        self.test_data_folder = test_data_folder
        self.csv_path = os.path.join(test_data_folder, "sppc_project_portfolio.csv")
        self.results: Dict[str, List[TestResult]] = {}
        self.summaries: Dict[str, ProviderSummary] = {}

    def verify_provider(self, provider: LLMProvider) -> bool:
        """Verify provider is working"""
        print(f"  Verifying {provider.value}...")
        result = test_provider(provider)
        if result["success"]:
            print(f"  ✓ {provider.value} is working ({result['latency_ms']:.0f}ms)")
            return True
        else:
            print(f"  ✗ {provider.value} failed: {result.get('error', 'Unknown error')}")
            return False

    def run_goal1_tests(self, provider: LLMProvider) -> List[TestResult]:
        """Run Goal 1 calculation tests"""
        results = []

        try:
            calc_results = run_calculation_tests(provider, self.csv_path)

            # Map results to test cases
            test_mapping = {
                "1.1_single_energy": "1.1",
                "1.2_total_revenue": "1.2",
                "1.3_revenue_per_mw": "1.3",
                "1.4_weighted_tariff": "1.4",
                "1.5_verify_revenue": "1.5",
                "1.6_nonexistent": "1.6",
            }

            for result_key, test_id in test_mapping.items():
                if result_key in calc_results:
                    calc_result = calc_results[result_key]
                    test_case = next((t for t in TEST_CASES if t.id == test_id), None)

                    results.append(TestResult(
                        test_id=test_id,
                        test_name=test_case.name if test_case else result_key,
                        provider=provider.value,
                        passed=calc_result.success,
                        latency_ms=calc_result.total_latency_ms,
                        steps=[{
                            "step": s.step_number,
                            "action": s.action,
                            "status": s.status.value,
                            "result": str(s.result)[:200] if s.result else None,
                            "error": s.error,
                            "latency_ms": s.latency_ms
                        } for s in calc_result.steps],
                        final_answer=calc_result.final_answer,
                        raw_response=calc_result.raw_llm_response[:500] if calc_result.raw_llm_response else ""
                    ))
        except Exception as e:
            # If tests fail completely, add error results
            for test_id in ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]:
                test_case = next((t for t in TEST_CASES if t.id == test_id), None)
                results.append(TestResult(
                    test_id=test_id,
                    test_name=test_case.name if test_case else test_id,
                    provider=provider.value,
                    passed=False,
                    latency_ms=0,
                    steps=[],
                    final_answer=None,
                    raw_response="",
                    error=str(e)
                ))

        return results

    def run_goal2_tests(self, provider: LLMProvider) -> List[TestResult]:
        """Run Goal 2 logic tests"""
        results = []

        try:
            logic_results = run_logic_tests(provider)

            test_mapping = {
                "2.1_eligible": "2.1",
                "2.2_disqualified": "2.2",
                "2.3_multiple_failures": "2.3",
                "2.4_bond_required": "2.4",
                "2.5_what_if": "2.5",
                "2.6_ranking": "2.6",
            }

            for result_key, test_id in test_mapping.items():
                if result_key in logic_results:
                    logic_result = logic_results[result_key]
                    test_case = next((t for t in TEST_CASES if t.id == test_id), None)

                    results.append(TestResult(
                        test_id=test_id,
                        test_name=test_case.name if test_case else result_key,
                        provider=provider.value,
                        passed=logic_result.success,
                        latency_ms=logic_result.total_latency_ms,
                        steps=[{
                            "step": s.step_number,
                            "action": s.action,
                            "status": s.status.value,
                            "result": str(s.result)[:200] if s.result else None,
                            "error": s.error,
                            "latency_ms": s.latency_ms
                        } for s in logic_result.steps],
                        final_answer=logic_result.final_answer,
                        raw_response=logic_result.raw_llm_response[:500] if logic_result.raw_llm_response else ""
                    ))
        except Exception as e:
            for test_id in ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6"]:
                test_case = next((t for t in TEST_CASES if t.id == test_id), None)
                results.append(TestResult(
                    test_id=test_id,
                    test_name=test_case.name if test_case else test_id,
                    provider=provider.value,
                    passed=False,
                    latency_ms=0,
                    steps=[],
                    final_answer=None,
                    raw_response="",
                    error=str(e)
                ))

        return results

    def run_goal3_tests(self, provider: LLMProvider) -> List[TestResult]:
        """Run Goal 3 retrieval tests"""
        results = []

        try:
            retrieval_results = run_retrieval_tests(provider, self.test_data_folder)

            test_mapping = {
                "3.1_beginning": "3.1",
                "3.2_middle": "3.2",
                "3.3_end": "3.3",
                "3.4_cross_doc": "3.4",
                "3.5_nonexistent": "3.5",
                "3.6_citation": "3.6",
            }

            for result_key, test_id in test_mapping.items():
                if result_key in retrieval_results:
                    ret_result = retrieval_results[result_key]
                    test_case = next((t for t in TEST_CASES if t.id == test_id), None)

                    results.append(TestResult(
                        test_id=test_id,
                        test_name=test_case.name if test_case else result_key,
                        provider=provider.value,
                        passed=ret_result.success,
                        latency_ms=ret_result.total_latency_ms,
                        steps=[{
                            "step": s.step_number,
                            "action": s.action,
                            "status": s.status.value,
                            "result": str(s.result)[:200] if s.result else None,
                            "error": s.error,
                            "latency_ms": s.latency_ms
                        } for s in ret_result.steps],
                        final_answer=ret_result.final_answer,
                        raw_response=ret_result.raw_llm_response[:500] if ret_result.raw_llm_response else ""
                    ))
        except Exception as e:
            for test_id in ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6"]:
                test_case = next((t for t in TEST_CASES if t.id == test_id), None)
                results.append(TestResult(
                    test_id=test_id,
                    test_name=test_case.name if test_case else test_id,
                    provider=provider.value,
                    passed=False,
                    latency_ms=0,
                    steps=[],
                    final_answer=None,
                    raw_response="",
                    error=str(e)
                ))

        return results

    def run_all_tests(self, provider: LLMProvider) -> List[TestResult]:
        """Run all tests for a provider"""
        all_results = []

        print(f"\n{'='*60}")
        print(f"Running tests for: {provider.value}")
        print(f"{'='*60}")

        # Verify provider first
        if not self.verify_provider(provider):
            print(f"  Skipping {provider.value} - provider not available")
            # Return failed results for all tests
            for test_case in TEST_CASES:
                all_results.append(TestResult(
                    test_id=test_case.id,
                    test_name=test_case.name,
                    provider=provider.value,
                    passed=False,
                    latency_ms=0,
                    steps=[],
                    final_answer=None,
                    raw_response="",
                    error="Provider not available"
                ))
            return all_results

        # Run Goal 1 tests
        print("\n  Goal 1: Mathematical Calculations")
        print("  " + "-" * 40)
        goal1_results = self.run_goal1_tests(provider)
        all_results.extend(goal1_results)
        for r in goal1_results:
            status = "✅" if r.passed else "❌"
            print(f"    {status} {r.test_id}: {r.test_name} ({r.latency_ms:.0f}ms)")

        # Run Goal 2 tests
        print("\n  Goal 2: Multi-Condition Logic")
        print("  " + "-" * 40)
        goal2_results = self.run_goal2_tests(provider)
        all_results.extend(goal2_results)
        for r in goal2_results:
            status = "✅" if r.passed else "❌"
            print(f"    {status} {r.test_id}: {r.test_name} ({r.latency_ms:.0f}ms)")

        # Run Goal 3 tests
        print("\n  Goal 3: Long-Context Retrieval")
        print("  " + "-" * 40)
        goal3_results = self.run_goal3_tests(provider)
        all_results.extend(goal3_results)
        for r in goal3_results:
            status = "✅" if r.passed else "❌"
            print(f"    {status} {r.test_id}: {r.test_name} ({r.latency_ms:.0f}ms)")

        return all_results

    def compute_summary(self, provider: str, results: List[TestResult]) -> ProviderSummary:
        """Compute summary statistics for a provider"""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        goal1_results = [r for r in results if r.test_id.startswith("1.")]
        goal2_results = [r for r in results if r.test_id.startswith("2.")]
        goal3_results = [r for r in results if r.test_id.startswith("3.")]

        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return ProviderSummary(
            provider=provider,
            total_tests=total,
            passed=passed,
            failed=failed,
            pass_rate=round(passed / total * 100, 1) if total > 0 else 0,
            avg_latency_ms=round(avg_latency, 1),
            goal1_passed=sum(1 for r in goal1_results if r.passed),
            goal1_total=len(goal1_results),
            goal2_passed=sum(1 for r in goal2_results if r.passed),
            goal2_total=len(goal2_results),
            goal3_passed=sum(1 for r in goal3_results if r.passed),
            goal3_total=len(goal3_results),
        )

    def run(self, providers: List[LLMProvider]) -> Dict[str, Any]:
        """Run all tests for all providers and return results"""
        print("\n" + "=" * 60)
        print("SPPC API COMPARISON TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Test Data: {self.test_data_folder}")
        print(f"Providers: {', '.join(p.value for p in providers)}")
        print(f"Total Test Cases: {len(TEST_CASES)}")

        start_time = time.time()

        for provider in providers:
            results = self.run_all_tests(provider)
            self.results[provider.value] = results
            self.summaries[provider.value] = self.compute_summary(provider.value, results)

        total_time = time.time() - start_time

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        for provider, summary in self.summaries.items():
            print(f"\n{provider.upper()}:")
            print(f"  Pass Rate: {summary.passed}/{summary.total_tests} ({summary.pass_rate}%)")
            print(f"  Goal 1 (Math): {summary.goal1_passed}/{summary.goal1_total}")
            print(f"  Goal 2 (Logic): {summary.goal2_passed}/{summary.goal2_total}")
            print(f"  Goal 3 (Retrieval): {summary.goal3_passed}/{summary.goal3_total}")
            print(f"  Avg Latency: {summary.avg_latency_ms:.0f}ms")

        print(f"\nTotal Execution Time: {total_time:.1f}s")

        # Return structured results
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_data_folder": self.test_data_folder,
                "providers": [p.value for p in providers],
                "total_test_cases": len(TEST_CASES),
                "execution_time_seconds": round(total_time, 2)
            },
            "test_cases": [asdict(tc) for tc in TEST_CASES],
            "results": {
                provider: [asdict(r) for r in results]
                for provider, results in self.results.items()
            },
            "summaries": {
                provider: asdict(summary)
                for provider, summary in self.summaries.items()
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Run API comparison tests")
    parser.add_argument(
        "--providers",
        type=str,
        default="openai",
        help="Comma-separated list of providers: openai,ollama,custom"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_results.json",
        help="Output file for results JSON"
    )

    args = parser.parse_args()

    # Parse providers
    provider_map = {
        "openai": LLMProvider.OPENAI,
        "ollama": LLMProvider.OLLAMA,
        "custom": LLMProvider.CUSTOM
    }

    providers = []
    for p in args.providers.split(","):
        p = p.strip().lower()
        if p in provider_map:
            providers.append(provider_map[p])
        else:
            print(f"Warning: Unknown provider '{p}', skipping")

    if not providers:
        print("Error: No valid providers specified")
        sys.exit(1)

    # Get test data folder
    test_data_folder = os.path.join(os.path.dirname(__file__), "test_data")

    # Run tests
    runner = TestRunner(test_data_folder)
    results = runner.run(providers)

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()

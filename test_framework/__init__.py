"""
SPPC API Comparison Test Framework

This module provides tools for testing and comparing LLM API capabilities.

Usage:
    # Run tests
    python run_tests.py --providers openai,custom

    # Generate report
    python report_generator.py --input test_results.json
"""

from .test_runner import TestRunner, TEST_CASES
from .report_generator import ReportGenerator
from .calculation_agent import CalculationAgent
from .logic_agent import LogicAgent
from .retrieval_agent import RetrievalAgent

__all__ = [
    "TestRunner",
    "TEST_CASES",
    "ReportGenerator",
    "CalculationAgent",
    "LogicAgent",
    "RetrievalAgent",
]

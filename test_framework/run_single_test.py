#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run a single calculation test to verify the framework works"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm_provider import LLMProvider
from calculation_agent import CalculationAgent

def main():
    print("=" * 60)
    print("LLM Evaluation - Single Test Run")
    print("=" * 60)

    data_path = os.path.join(os.path.dirname(__file__), "test_data", "sppc_project_portfolio.csv")

    print(f"\nData file: {data_path}")
    print(f"Provider: Ollama (gpt-oss)")
    print("\nCreating agent...")

    agent = CalculationAgent(provider=LLMProvider.OLLAMA, data_path=data_path)
    print(f"Loaded {len(agent.df)} rows of data")

    print("\n" + "-" * 60)
    print("TEST: Calculate annual energy for first project")
    print("-" * 60)

    # Get first project name
    project_name = agent.df.iloc[0]['Project_Name']
    print(f"Project: {project_name}")

    result = agent.calculate_annual_energy(project_name)

    print(f"\nResult: {'PASS' if result.success else 'FAIL'}")
    print(f"Latency: {result.total_latency_ms:.0f}ms")
    print(f"\nAnswer: {result.final_answer}")

    if result.raw_llm_response:
        print(f"\nRaw LLM Response (first 500 chars):")
        print(result.raw_llm_response[:500])

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()

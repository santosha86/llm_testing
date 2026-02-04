#!/usr/bin/env python
"""
SPPC API Comparison Test Suite - Main Entry Point

This script runs the complete test suite and generates comparison reports.

Usage Examples:
    # Test with OpenAI only (baseline)
    python run_tests.py --providers openai

    # Compare OpenAI vs Custom API
    python run_tests.py --providers openai,custom

    # Compare all providers
    python run_tests.py --providers openai,ollama,custom

    # Run tests and auto-open report
    python run_tests.py --providers openai,custom --open-report
"""

import os
import sys
import argparse
import webbrowser
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

from backend.llm_provider import LLMProvider
from test_runner import TestRunner
from report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="SPPC API Comparison Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --providers openai
  python run_tests.py --providers openai,custom
  python run_tests.py --providers openai,custom --open-report

Environment Variables Required:
  For OpenAI:   OPENAI_API_KEY
  For Ollama:   (Ollama must be running locally)
  For Custom:   CUSTOM_API_BASE_URL, CUSTOM_API_KEY
        """
    )

    parser.add_argument(
        "--providers",
        type=str,
        default="openai",
        help="Comma-separated providers: openai,ollama,custom (default: openai)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: test_framework/)"
    )

    parser.add_argument(
        "--open-report",
        action="store_true",
        help="Open the HTML report in browser after generation"
    )

    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Skip report generation (only output JSON)"
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
            print(f"⚠️  Warning: Unknown provider '{p}', skipping")

    if not providers:
        print("❌ Error: No valid providers specified")
        print("   Valid providers: openai, ollama, custom")
        sys.exit(1)

    # Set output directory
    output_dir = args.output_dir or os.path.dirname(__file__)
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"test_results_{timestamp}.json"
    html_filename = f"api_comparison_report_{timestamp}.html"

    json_path = os.path.join(output_dir, json_filename)
    html_path = os.path.join(output_dir, html_filename)

    # Get test data folder
    test_data_folder = os.path.join(os.path.dirname(__file__), "test_data")

    print("\n" + "=" * 60)
    print("🚀 SPPC API COMPARISON TEST SUITE")
    print("=" * 60)

    # Check for required environment variables
    print("\n📋 Checking configuration...")
    for provider in providers:
        if provider == LLMProvider.OPENAI:
            if not os.getenv("OPENAI_API_KEY"):
                print(f"   ⚠️  OPENAI_API_KEY not set - OpenAI tests may fail")
            else:
                print(f"   ✓ OpenAI API key configured")
        elif provider == LLMProvider.CUSTOM:
            if not os.getenv("CUSTOM_API_BASE_URL"):
                print(f"   ⚠️  CUSTOM_API_BASE_URL not set - Custom API tests may fail")
            else:
                print(f"   ✓ Custom API configured: {os.getenv('CUSTOM_API_BASE_URL')}")
        elif provider == LLMProvider.OLLAMA:
            print(f"   ℹ️  Ollama - ensure server is running at localhost:11434")

    # Run tests
    print(f"\n📁 Test Data: {test_data_folder}")
    print(f"🤖 Providers: {', '.join(p.value for p in providers)}")

    runner = TestRunner(test_data_folder)
    results = runner.run(providers)

    # Save JSON results
    import json
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Results saved: {json_path}")

    # Generate HTML report
    if not args.skip_report:
        print("\n📊 Generating HTML report...")
        generator = ReportGenerator(results)
        generator.save(html_path)

        # Also save as latest
        latest_html = os.path.join(output_dir, "api_comparison_report_latest.html")
        generator.save(latest_html)

        if args.open_report:
            print("🌐 Opening report in browser...")
            webbrowser.open(f"file://{os.path.abspath(html_path)}")

    print("\n" + "=" * 60)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 60)
    print(f"\nFiles generated:")
    print(f"   📄 {json_path}")
    if not args.skip_report:
        print(f"   📊 {html_path}")
        print(f"   📊 {latest_html}")

    # Print quick summary
    print("\n📈 Quick Summary:")
    for provider, summary in results.get("summaries", {}).items():
        pass_rate = summary.get("pass_rate", 0)
        emoji = "✅" if pass_rate >= 80 else "⚠️" if pass_rate >= 50 else "❌"
        print(f"   {emoji} {provider.upper()}: {pass_rate}% pass rate ({summary.get('passed', 0)}/{summary.get('total_tests', 0)})")


if __name__ == "__main__":
    main()

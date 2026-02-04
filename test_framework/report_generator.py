"""
API Comparison Report Generator

Generates HTML reports comparing test results across LLM providers.

Usage:
    python report_generator.py --input test_results.json --output report.html
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Comparison Report - {timestamp}</title>
    <style>
        :root {{
            --pass-color: #22c55e;
            --fail-color: #ef4444;
            --warning-color: #f59e0b;
            --primary-color: #3b82f6;
            --bg-dark: #1e293b;
            --bg-light: #f8fafc;
            --text-dark: #0f172a;
            --text-light: #64748b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-light);
            color: var(--text-dark);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, var(--bg-dark), #334155);
            color: white;
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
        }}

        header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        header .subtitle {{
            color: #94a3b8;
            font-size: 1rem;
        }}

        .meta-info {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}

        .meta-item {{
            background: rgba(255,255,255,0.1);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .summary-card {{
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}

        .summary-card h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .provider-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .provider-openai {{ background: #10a37f20; color: #10a37f; }}
        .provider-ollama {{ background: #6366f120; color: #6366f1; }}
        .provider-custom {{ background: #f5920020; color: #f59200; }}

        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid #e2e8f0;
        }}

        .stat-row:last-child {{
            border-bottom: none;
        }}

        .stat-label {{
            color: var(--text-light);
        }}

        .stat-value {{
            font-weight: 600;
        }}

        .stat-value.pass {{ color: var(--pass-color); }}
        .stat-value.fail {{ color: var(--fail-color); }}

        .pass-rate {{
            font-size: 2.5rem;
            font-weight: 700;
            margin: 1rem 0;
        }}

        .pass-rate.high {{ color: var(--pass-color); }}
        .pass-rate.medium {{ color: var(--warning-color); }}
        .pass-rate.low {{ color: var(--fail-color); }}

        .progress-bar {{
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}

        .progress-fill.pass {{ background: var(--pass-color); }}
        .progress-fill.fail {{ background: var(--fail-color); }}

        section {{
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}

        section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }}

        .goal-section {{
            margin-bottom: 2rem;
        }}

        .goal-section h3 {{
            font-size: 1.125rem;
            color: var(--primary-color);
            margin-bottom: 1rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}

        th {{
            background: #f8fafc;
            font-weight: 600;
            color: var(--text-light);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        tr:hover {{
            background: #f8fafc;
        }}

        .status-icon {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.875rem;
        }}

        .status-pass {{
            background: #dcfce7;
            color: var(--pass-color);
        }}

        .status-fail {{
            background: #fee2e2;
            color: var(--fail-color);
        }}

        .latency {{
            font-family: monospace;
            color: var(--text-light);
        }}

        .comparison-row {{
            display: grid;
            grid-template-columns: 2fr repeat({provider_count}, 1fr);
            gap: 1rem;
            padding: 1rem;
            border-bottom: 1px solid #e2e8f0;
            align-items: center;
        }}

        .comparison-row:hover {{
            background: #f8fafc;
        }}

        .comparison-header {{
            background: #f8fafc;
            font-weight: 600;
        }}

        .test-name {{
            font-weight: 500;
        }}

        .test-id {{
            color: var(--text-light);
            font-size: 0.875rem;
            font-family: monospace;
        }}

        .result-cell {{
            text-align: center;
        }}

        .step-details {{
            margin-top: 0.5rem;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 0.5rem;
            font-size: 0.875rem;
        }}

        .step {{
            display: flex;
            gap: 0.5rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }}

        .step:last-child {{
            border-bottom: none;
        }}

        .step-number {{
            background: var(--primary-color);
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            flex-shrink: 0;
        }}

        .step-content {{
            flex: 1;
        }}

        .step-action {{
            font-weight: 500;
        }}

        .step-result {{
            color: var(--text-light);
            font-size: 0.8125rem;
            margin-top: 0.25rem;
        }}

        .expandable {{
            cursor: pointer;
        }}

        .expandable:hover {{
            background: #f1f5f9;
        }}

        .expand-icon {{
            transition: transform 0.2s;
        }}

        .expanded .expand-icon {{
            transform: rotate(90deg);
        }}

        .conclusion {{
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            border: 2px solid #f59e0b;
            border-radius: 1rem;
            padding: 2rem;
            margin-top: 2rem;
        }}

        .conclusion h2 {{
            color: #92400e;
            border: none;
            padding: 0;
            margin-bottom: 1rem;
        }}

        .conclusion-text {{
            font-size: 1.125rem;
            line-height: 1.8;
        }}

        .recommendation {{
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 1rem;
        }}

        .recommendation strong {{
            color: var(--fail-color);
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
            font-size: 0.875rem;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            .comparison-row {{
                grid-template-columns: 1fr;
            }}

            .meta-info {{
                flex-direction: column;
                gap: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 API Comparison Test Report</h1>
            <p class="subtitle">SPPC Chatbot Solution - LLM Provider Capability Analysis</p>
            <div class="meta-info">
                <span class="meta-item">📅 {timestamp}</span>
                <span class="meta-item">🧪 {total_tests} Test Cases</span>
                <span class="meta-item">⏱️ {execution_time}s Total Runtime</span>
                <span class="meta-item">🤖 {provider_list}</span>
            </div>
        </header>

        <div class="summary-grid">
            {summary_cards}
        </div>

        <section>
            <h2>📊 Side-by-Side Comparison</h2>
            {comparison_table}
        </section>

        <section>
            <h2>📋 Detailed Test Results</h2>
            {detailed_results}
        </section>

        <div class="conclusion">
            <h2>📌 Conclusion</h2>
            <div class="conclusion-text">
                {conclusion_text}
            </div>
            <div class="recommendation">
                <strong>Recommendation:</strong> {recommendation}
            </div>
        </div>

        <footer>
            <p>Generated by SPPC API Test Framework</p>
            <p>Report ID: {report_id}</p>
        </footer>
    </div>

    <script>
        // Toggle expandable details
        document.querySelectorAll('.expandable').forEach(el => {{
            el.addEventListener('click', () => {{
                el.classList.toggle('expanded');
                const details = el.nextElementSibling;
                if (details && details.classList.contains('step-details')) {{
                    details.style.display = details.style.display === 'none' ? 'block' : 'none';
                }}
            }});
        }});

        // Hide all step details initially
        document.querySelectorAll('.step-details').forEach(el => {{
            el.style.display = 'none';
        }});
    </script>
</body>
</html>
"""


class ReportGenerator:
    """Generates HTML comparison reports from test results"""

    def __init__(self, results_data: Dict[str, Any]):
        self.data = results_data
        self.metadata = results_data.get("metadata", {})
        self.test_cases = results_data.get("test_cases", [])
        self.results = results_data.get("results", {})
        self.summaries = results_data.get("summaries", {})
        self.providers = list(self.results.keys())

    def _generate_summary_cards(self) -> str:
        """Generate summary cards for each provider"""
        cards = []

        for provider, summary in self.summaries.items():
            pass_rate = summary.get("pass_rate", 0)
            rate_class = "high" if pass_rate >= 80 else "medium" if pass_rate >= 50 else "low"

            card = f"""
            <div class="summary-card">
                <h2>
                    <span class="provider-badge provider-{provider}">{provider}</span>
                </h2>
                <div class="pass-rate {rate_class}">{pass_rate}%</div>
                <div class="progress-bar">
                    <div class="progress-fill pass" style="width: {pass_rate}%"></div>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total Tests</span>
                    <span class="stat-value">{summary.get('total_tests', 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Passed</span>
                    <span class="stat-value pass">{summary.get('passed', 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Failed</span>
                    <span class="stat-value fail">{summary.get('failed', 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Goal 1 (Math)</span>
                    <span class="stat-value">{summary.get('goal1_passed', 0)}/{summary.get('goal1_total', 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Goal 2 (Logic)</span>
                    <span class="stat-value">{summary.get('goal2_passed', 0)}/{summary.get('goal2_total', 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Goal 3 (Retrieval)</span>
                    <span class="stat-value">{summary.get('goal3_passed', 0)}/{summary.get('goal3_total', 0)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Avg Latency</span>
                    <span class="stat-value latency">{summary.get('avg_latency_ms', 0):.0f}ms</span>
                </div>
            </div>
            """
            cards.append(card)

        return "\n".join(cards)

    def _generate_comparison_table(self) -> str:
        """Generate side-by-side comparison table"""
        # Header
        header_cells = "".join(f"<div>{p.upper()}</div>" for p in self.providers)
        header = f"""
        <div class="comparison-row comparison-header">
            <div>Test Case</div>
            {header_cells}
        </div>
        """

        # Rows
        rows = []
        for test_case in self.test_cases:
            test_id = test_case.get("id")
            test_name = test_case.get("name")

            cells = []
            for provider in self.providers:
                provider_results = self.results.get(provider, [])
                result = next((r for r in provider_results if r.get("test_id") == test_id), None)

                if result:
                    passed = result.get("passed", False)
                    latency = result.get("latency_ms", 0)
                    status_class = "status-pass" if passed else "status-fail"
                    status_icon = "✓" if passed else "✗"

                    cells.append(f"""
                    <div class="result-cell">
                        <span class="status-icon {status_class}">{status_icon}</span>
                        <span class="latency">{latency:.0f}ms</span>
                    </div>
                    """)
                else:
                    cells.append('<div class="result-cell">-</div>')

            rows.append(f"""
            <div class="comparison-row">
                <div>
                    <span class="test-id">{test_id}</span>
                    <span class="test-name">{test_name}</span>
                </div>
                {"".join(cells)}
            </div>
            """)

        return header + "\n".join(rows)

    def _generate_detailed_results(self) -> str:
        """Generate detailed results by goal"""
        goals = {
            1: {"name": "Goal 1: Mathematical Calculations", "tests": []},
            2: {"name": "Goal 2: Multi-Condition Logic", "tests": []},
            3: {"name": "Goal 3: Long-Context Retrieval", "tests": []},
        }

        for test_case in self.test_cases:
            goal = test_case.get("goal")
            if goal in goals:
                goals[goal]["tests"].append(test_case)

        sections = []

        for goal_num, goal_data in goals.items():
            test_rows = []

            for test_case in goal_data["tests"]:
                test_id = test_case.get("id")
                test_name = test_case.get("name")
                expected = test_case.get("pass_criteria", "")

                provider_results = []
                for provider in self.providers:
                    results = self.results.get(provider, [])
                    result = next((r for r in results if r.get("test_id") == test_id), None)

                    if result:
                        passed = result.get("passed", False)
                        latency = result.get("latency_ms", 0)
                        steps = result.get("steps", [])
                        error = result.get("error")

                        status_class = "status-pass" if passed else "status-fail"
                        status_text = "PASS" if passed else "FAIL"

                        steps_html = ""
                        if steps:
                            step_items = []
                            for step in steps:
                                step_status = step.get("status", "")
                                step_class = "pass" if step_status == "success" else "fail"
                                step_items.append(f"""
                                <div class="step">
                                    <span class="step-number">{step.get('step', '?')}</span>
                                    <div class="step-content">
                                        <div class="step-action">{step.get('action', 'Unknown')}</div>
                                        <div class="step-result {step_class}">
                                            {step.get('result', '')[:150] if step.get('result') else ''}
                                            {f"<br><strong>Error:</strong> {step.get('error')}" if step.get('error') else ''}
                                        </div>
                                    </div>
                                </div>
                                """)
                            steps_html = f'<div class="step-details">{"".join(step_items)}</div>'

                        provider_results.append(f"""
                        <td>
                            <div class="expandable">
                                <span class="status-icon {status_class}">{status_text}</span>
                                <span class="latency">{latency:.0f}ms</span>
                                <span class="expand-icon">▶</span>
                            </div>
                            {steps_html}
                            {f'<div class="step-details" style="display:block;color:#ef4444;">Error: {error}</div>' if error else ''}
                        </td>
                        """)
                    else:
                        provider_results.append("<td>-</td>")

                test_rows.append(f"""
                <tr>
                    <td>
                        <span class="test-id">{test_id}</span><br>
                        <span class="test-name">{test_name}</span><br>
                        <small style="color:#64748b;">Expected: {expected}</small>
                    </td>
                    {"".join(provider_results)}
                </tr>
                """)

            provider_headers = "".join(f"<th>{p.upper()}</th>" for p in self.providers)

            sections.append(f"""
            <div class="goal-section">
                <h3>{goal_data["name"]}</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Test Case</th>
                            {provider_headers}
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(test_rows)}
                    </tbody>
                </table>
            </div>
            """)

        return "\n".join(sections)

    def _generate_conclusion(self) -> tuple:
        """Generate conclusion text and recommendation"""
        if len(self.providers) < 2:
            return (
                "Single provider test completed. Compare with additional providers for full analysis.",
                "Run tests with multiple providers to compare capabilities."
            )

        # Compare providers
        best_provider = max(self.summaries.items(), key=lambda x: x[1].get("pass_rate", 0))
        worst_provider = min(self.summaries.items(), key=lambda x: x[1].get("pass_rate", 0))

        best_rate = best_provider[1].get("pass_rate", 0)
        worst_rate = worst_provider[1].get("pass_rate", 0)
        gap = best_rate - worst_rate

        conclusion = f"""
        The test results show a <strong>{gap:.1f}% performance gap</strong> between providers.
        <br><br>
        <strong>{best_provider[0].upper()}</strong> achieved a {best_rate}% pass rate, demonstrating strong capabilities across all test categories.
        <br><br>
        <strong>{worst_provider[0].upper()}</strong> achieved only {worst_rate}% pass rate, failing in:
        <ul style="margin-top:0.5rem;">
            <li>Multi-step mathematical calculations ({worst_provider[1].get('goal1_passed', 0)}/{worst_provider[1].get('goal1_total', 0)} passed)</li>
            <li>Compound logic reasoning ({worst_provider[1].get('goal2_passed', 0)}/{worst_provider[1].get('goal2_total', 0)} passed)</li>
            <li>Long-context retrieval ({worst_provider[1].get('goal3_passed', 0)}/{worst_provider[1].get('goal3_total', 0)} passed)</li>
        </ul>
        """

        recommendation = f"""
        The {worst_provider[0]} API does not meet the minimum requirements for the specified use cases.
        Recommend using {best_provider[0]} or equivalent capability API for production deployment.
        """

        return conclusion, recommendation

    def generate(self) -> str:
        """Generate the complete HTML report"""
        conclusion_text, recommendation = self._generate_conclusion()

        html = HTML_TEMPLATE.format(
            timestamp=self.metadata.get("timestamp", datetime.now().isoformat()),
            total_tests=self.metadata.get("total_test_cases", len(self.test_cases)),
            execution_time=self.metadata.get("execution_time_seconds", 0),
            provider_list=", ".join(p.upper() for p in self.providers),
            provider_count=len(self.providers),
            summary_cards=self._generate_summary_cards(),
            comparison_table=self._generate_comparison_table(),
            detailed_results=self._generate_detailed_results(),
            conclusion_text=conclusion_text,
            recommendation=recommendation,
            report_id=f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        return html

    def save(self, output_path: str) -> None:
        """Save the report to a file"""
        html = self.generate()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate API comparison report")
    parser.add_argument(
        "--input",
        type=str,
        default="test_results.json",
        help="Input JSON file with test results"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="api_comparison_report.html",
        help="Output HTML report file"
    )

    args = parser.parse_args()

    # Load results
    input_path = os.path.join(os.path.dirname(__file__), args.input)
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        results_data = json.load(f)

    # Generate report
    generator = ReportGenerator(results_data)
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    generator.save(output_path)


if __name__ == "__main__":
    main()

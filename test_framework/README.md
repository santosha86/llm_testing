# SPPC API Comparison Test Framework

A comprehensive test suite for comparing LLM API capabilities across different providers.

## Purpose

This framework helps you:
1. **Validate** that your chatbot solution works with a capable API (OpenAI)
2. **Expose** limitations of customer-provided APIs
3. **Generate** professional reports showing exactly where/why APIs fail
4. **Document** evidence for customer discussions

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env.local` in the project root:

```env
# For OpenAI (baseline testing)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# For Customer API
CUSTOM_API_BASE_URL=https://api.customer.com/v1
CUSTOM_API_KEY=customer-api-key
CUSTOM_MODEL=customer-model-name
```

### 3. Run Tests

```bash
cd test_framework

# Test with OpenAI only (establish baseline)
python run_tests.py --providers openai

# Compare OpenAI vs Customer API
python run_tests.py --providers openai,custom

# Compare and auto-open report
python run_tests.py --providers openai,custom --open-report
```

## Test Cases

### Goal 1: Mathematical Calculations (6 tests)

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| 1.1 | Single project energy calculation | Correct: MW × 8760 × CF |
| 1.2 | Total revenue across all projects | Multi-step chain calculation |
| 1.3 | Rank by revenue per MW | Correct derived metric ranking |
| 1.4 | Weighted average tariff | Correct weighted average formula |
| 1.5 | Verify revenue column | Detect Tabarjal mismatch |
| 1.6 | Non-existent project query | Return "not found" (no hallucination) |

### Goal 2: Multi-Condition Logic (6 tests)

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| 2.1 | Identify eligible bidders | Correctly identify A, B, E |
| 2.2 | Disqualification reasons | Identify C, D with all reasons |
| 2.3 | Multiple rule failures | Bidder D fails 4 rules |
| 2.4 | Performance bond detection | B and E need bonds |
| 2.5 | What-if rule relaxation | C becomes eligible |
| 2.6 | Rank eligible bidders | E → B → A by tariff |

### Goal 3: Long-Context Retrieval (6 tests)

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| 3.1 | Retrieve from document beginning | March 15, 2023 |
| 3.2 | Retrieve from document middle | 1,400 MW available |
| 3.3 | Retrieve from document end | 58.7 GW target |
| 3.4 | Cross-document comparison | Find 1,400 vs 900 MW gap |
| 3.5 | Non-existent info query | "Not mentioned" (no hallucination) |
| 3.6 | Citation accuracy | Correct section reference |

## Test Data Files

Located in `test_framework/test_data/`:

- `sppc_project_portfolio.csv` - Renewable energy projects data
- `bidder_eligibility_rules.md` - Eligibility rules and bidder table
- `ecra_regulatory_framework.md` - Long regulatory document (simulates 35 pages)
- `sppc_round7_summary.md` - Second document for cross-referencing

## Output Files

After running tests, you'll find:

- `test_results_YYYYMMDD_HHMMSS.json` - Raw test results
- `api_comparison_report_YYYYMMDD_HHMMSS.html` - Visual comparison report
- `api_comparison_report_latest.html` - Always points to latest report

## Report Structure

The HTML report includes:

1. **Executive Summary** - Pass rates for each provider
2. **Side-by-Side Comparison** - Quick view of all test results
3. **Detailed Results** - Step-by-step execution logs
4. **Conclusion** - Automated analysis and recommendation

## Adding Custom API Provider

1. Set environment variables:
```env
CUSTOM_API_BASE_URL=https://your-api.com/v1
CUSTOM_API_KEY=your-key
CUSTOM_MODEL=model-name
```

2. The custom API must be OpenAI-compatible (same request/response format)

3. Run tests:
```bash
python run_tests.py --providers openai,custom
```

## Expected Results

When comparing a capable API (OpenAI GPT-4) vs a limited API:

| Provider | Expected Pass Rate |
|----------|-------------------|
| OpenAI GPT-4 | 80-95% |
| Limited/Smaller Models | 20-40% |

## Troubleshooting

### "OPENAI_API_KEY not set"
- Ensure `.env.local` exists in project root
- Verify the key is correct

### "Provider not available"
- For Ollama: Ensure Ollama is running (`ollama serve`)
- For Custom: Verify the base URL is accessible

### Tests timing out
- Increase timeout in `llm_provider.py`
- Check API rate limits

## File Structure

```
test_framework/
├── run_tests.py           # Main entry point
├── test_runner.py         # Test orchestration
├── report_generator.py    # HTML report generation
├── calculation_agent.py   # Goal 1: Math tests
├── logic_agent.py         # Goal 2: Logic tests
├── retrieval_agent.py     # Goal 3: Retrieval tests
├── test_data/
│   ├── sppc_project_portfolio.csv
│   ├── bidder_eligibility_rules.md
│   ├── ecra_regulatory_framework.md
│   └── sppc_round7_summary.md
└── README.md
```

## Support

For issues or questions, check the main project documentation or contact the development team.

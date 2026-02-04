"""Quick test to verify the test framework works"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("LLM Evaluation Framework - Quick Test")
print("=" * 60)

# Test 1: Import check
print("\n[1/4] Checking imports...")
try:
    from backend.llm_provider import get_llm, LLMProvider
    print("  ✓ LLM provider imported")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# Test 2: Load Ollama LLM
print("\n[2/4] Loading Ollama LLM (gpt-oss)...")
try:
    llm = get_llm(LLMProvider.OLLAMA)
    print(f"  ✓ LLM loaded: {type(llm).__name__}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# Test 3: Simple LLM call
print("\n[3/4] Testing simple LLM call...")
try:
    from langchain_core.messages import HumanMessage
    response = llm.invoke([HumanMessage(content="What is 2 + 2? Reply with just the number.")])
    print(f"  ✓ Response: {response.content[:100]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# Test 4: Load test data
print("\n[4/4] Loading test data...")
try:
    import pandas as pd
    df = pd.read_csv("test_data/sppc_project_portfolio.csv")
    print(f"  ✓ Loaded {len(df)} projects from CSV")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("Quick test completed successfully!")
print("=" * 60)

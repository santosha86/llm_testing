"""
Document Retrieval Agent for Long-Context and Cross-Document Reasoning

This agent handles:
- Retrieval from different positions in long documents
- Cross-document data correlation
- Hallucination detection (refusing to answer when info doesn't exist)
- Citation accuracy

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
    """Represents a single step in the retrieval process"""
    step_number: int
    action: str
    expected_behavior: str
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0


@dataclass
class RetrievalResult:
    """Result of a retrieval task"""
    success: bool
    final_answer: Any
    steps: List[ExecutionStep] = field(default_factory=list)
    total_latency_ms: float = 0
    provider: str = ""
    raw_llm_response: str = ""
    citation: Optional[str] = None


class RetrievalAgent:
    """Agent for document retrieval and cross-document reasoning"""

    def __init__(self, provider: LLMProvider = None):
        """
        Initialize the retrieval agent.

        Args:
            provider: LLM provider to use (defaults to env setting)
        """
        self.provider = provider
        self.llm = get_llm(provider=provider, json_mode=True)
        self.documents = {}

    def load_document(self, name: str, path: str) -> None:
        """Load a document from file"""
        with open(path, 'r', encoding='utf-8') as f:
            self.documents[name] = f.read()

    def load_documents_from_folder(self, folder_path: str) -> None:
        """Load all markdown documents from a folder"""
        for filename in os.listdir(folder_path):
            if filename.endswith('.md'):
                name = filename.replace('.md', '')
                path = os.path.join(folder_path, filename)
                self.load_document(name, path)

    def _build_system_prompt(self, document_names: List[str] = None) -> str:
        """Build system prompt with document content"""
        if document_names is None:
            document_names = list(self.documents.keys())

        doc_content = ""
        for name in document_names:
            if name in self.documents:
                doc_content += f"\n\n{'='*60}\nDOCUMENT: {name}\n{'='*60}\n\n{self.documents[name]}"

        return f"""You are a document analysis assistant. You have access to the following documents:

{doc_content}

IMPORTANT RULES:
1. Only answer based on information EXPLICITLY stated in the documents
2. If information is NOT in the documents, say "This information is not mentioned in the provided documents"
3. NEVER make up or infer information that isn't explicitly stated
4. When citing information, reference the document name and section
5. For numerical data, quote the exact values from the documents

RESPONSE FORMAT (JSON only):
{{
    "answer": "Your answer based on the documents",
    "found_in_document": "document name" or null if not found,
    "section_reference": "Chapter/Section where found" or null,
    "exact_quote": "Relevant quote from document" or null,
    "confidence": "high" or "medium" or "low",
    "not_found": true/false (true if information doesn't exist in documents)
}}
"""

    def execute(self, query: str, documents: List[str] = None) -> RetrievalResult:
        """
        Execute a retrieval query.

        Args:
            query: Question to answer from documents
            documents: List of document names to search (default: all)

        Returns:
            RetrievalResult with steps and answer
        """
        start_time = time.time()
        steps = []

        # Step 1: Load documents
        step1 = ExecutionStep(
            step_number=1,
            action="Load document context",
            expected_behavior="Successfully load requested documents"
        )

        try:
            doc_names = documents or list(self.documents.keys())
            if not doc_names or not self.documents:
                raise ValueError("No documents loaded")

            step1.status = StepStatus.SUCCESS
            step1.result = f"Loaded {len(doc_names)} documents: {', '.join(doc_names)}"
            step1.latency_ms = (time.time() - start_time) * 1000
        except Exception as e:
            step1.status = StepStatus.FAILED
            step1.error = str(e)
            steps.append(step1)
            return RetrievalResult(
                success=False,
                final_answer=None,
                steps=steps,
                total_latency_ms=(time.time() - start_time) * 1000,
                provider=self.provider.value if self.provider else "default"
            )

        steps.append(step1)

        # Step 2: Query LLM
        step2_start = time.time()
        step2 = ExecutionStep(
            step_number=2,
            action="Search and retrieve information",
            expected_behavior="LLM finds relevant information or correctly reports not found"
        )

        try:
            system_prompt = self._build_system_prompt(doc_names)

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
                return RetrievalResult(
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
            return RetrievalResult(
                success=False,
                final_answer=None,
                steps=steps,
                total_latency_ms=(time.time() - start_time) * 1000,
                provider=self.provider.value if self.provider else "default"
            )

        steps.append(step2)

        # Step 3: Validate response
        step3 = ExecutionStep(
            step_number=3,
            action="Validate response quality",
            expected_behavior="Check answer completeness and citation"
        )

        answer = result_data.get("answer")
        not_found = result_data.get("not_found", False)

        if answer or not_found:
            step3.status = StepStatus.SUCCESS
            if not_found:
                step3.result = "Correctly identified information as not present"
            else:
                step3.result = f"Answer found in: {result_data.get('found_in_document', 'unknown')}"
        else:
            step3.status = StepStatus.FAILED
            step3.error = "No answer provided"

        step3.latency_ms = 0
        steps.append(step3)

        total_latency = (time.time() - start_time) * 1000

        citation = None
        if result_data.get("found_in_document"):
            citation = f"{result_data.get('found_in_document')}: {result_data.get('section_reference', 'unknown section')}"

        return RetrievalResult(
            success=step3.status == StepStatus.SUCCESS,
            final_answer=result_data,
            steps=steps,
            total_latency_ms=total_latency,
            provider=self.provider.value if self.provider else "default",
            raw_llm_response=raw_response,
            citation=citation
        )

    # Test methods for Goal 3

    def retrieve_from_beginning(self) -> RetrievalResult:
        """Retrieve fact from beginning of ECRA document"""
        query = "When did this ECRA regulatory framework become effective? What date replaced the previous guidelines?"
        return self.execute(query, ["ecra_regulatory_framework"])

    def retrieve_from_middle(self) -> RetrievalResult:
        """Retrieve fact from middle of ECRA document"""
        query = "What is the available grid capacity for NEW renewable projects in the Northern Region according to the ECRA framework?"
        return self.execute(query, ["ecra_regulatory_framework"])

    def retrieve_from_end(self) -> RetrievalResult:
        """Retrieve fact from end of ECRA document"""
        query = "What is the NREP target for 2030 in terms of total renewable capacity, and how is it split between solar and wind?"
        return self.execute(query, ["ecra_regulatory_framework"])

    def retrieve_penalty_clause(self) -> RetrievalResult:
        """Retrieve specific penalty information"""
        query = "What is the penalty for projects that fail to achieve COD within 24 months of PPA signing? What is the penalty amount per MW per month?"
        return self.execute(query, ["ecra_regulatory_framework"])

    def cross_document_comparison(self) -> RetrievalResult:
        """Cross-reference data between two documents"""
        query = """Compare the Northern Region grid capacity information between the two documents:
        1. What does the ECRA regulatory framework say about available capacity in Northern Region?
        2. What does the SPPC Round 7 summary say about planned capacity allocation for Northern Region?
        3. Is there any conflict or gap between these two figures?"""
        return self.execute(query)  # Use all documents

    def query_nonexistent_info(self) -> RetrievalResult:
        """Query for information that doesn't exist (hallucination test)"""
        query = "What are the hydrogen production targets specified in the ECRA regulatory framework? What MW of hydrogen capacity is planned?"
        return self.execute(query, ["ecra_regulatory_framework"])

    def verify_citation_accuracy(self) -> RetrievalResult:
        """Test if citations are accurate"""
        query = "What is the minimum local content requirement for Year 3-4 (2025-2026) projects? Please cite the exact section."
        return self.execute(query, ["ecra_regulatory_framework"])


def run_retrieval_tests(provider: LLMProvider, test_data_folder: str) -> Dict[str, RetrievalResult]:
    """
    Run all retrieval tests for a given provider.

    Args:
        provider: LLM provider to test
        test_data_folder: Path to folder containing test documents

    Returns:
        Dictionary of test name -> RetrievalResult
    """
    agent = RetrievalAgent(provider=provider)

    # Load test documents
    agent.load_documents_from_folder(test_data_folder)

    results = {}

    # Test 3.1: Retrieve from beginning
    print(f"  Running Test 3.1: Retrieve from document beginning...")
    results["3.1_beginning"] = agent.retrieve_from_beginning()

    # Test 3.2: Retrieve from middle
    print(f"  Running Test 3.2: Retrieve from document middle...")
    results["3.2_middle"] = agent.retrieve_from_middle()

    # Test 3.3: Retrieve from end
    print(f"  Running Test 3.3: Retrieve from document end...")
    results["3.3_end"] = agent.retrieve_from_end()

    # Test 3.4: Cross-document comparison
    print(f"  Running Test 3.4: Cross-document comparison...")
    results["3.4_cross_doc"] = agent.cross_document_comparison()

    # Test 3.5: Query non-existent info (hallucination test)
    print(f"  Running Test 3.5: Non-existent information query...")
    results["3.5_nonexistent"] = agent.query_nonexistent_info()

    # Test 3.6: Citation accuracy
    print(f"  Running Test 3.6: Citation accuracy test...")
    results["3.6_citation"] = agent.verify_citation_accuracy()

    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    test_data_folder = os.path.join(
        os.path.dirname(__file__),
        "test_data"
    )

    print("Testing Retrieval Agent...")
    print(f"Documents folder: {test_data_folder}")
    print("-" * 50)

    try:
        results = run_retrieval_tests(LLMProvider.OPENAI, test_data_folder)
        for test_name, result in results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{test_name}: {status} ({result.total_latency_ms:.0f}ms)")
    except Exception as e:
        print(f"Error: {e}")

"""
PDF Agent wrapper with SSE streaming support for the LangGraph workflow.
Simple retrieval + true LLM streaming.
"""

import time
import json
from typing import Generator, List
from dataclasses import dataclass

from langchain_ollama import ChatOllama

# Import retriever from pdf_agent package
from ..pdf_agent.agents.tools import retrieve_context

# Import shared memory from parent
from ..memory import SharedMemory


@dataclass
class PDFAgentResponse:
    """Response from PDF agent."""
    content: str
    response_time: str
    sources: List[str]
    table_data: None = None
    sql_query: None = None

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "response_time": self.response_time,
            "sources": self.sources,
            "table_data": None,
            "sql_query": None
        }

llm = ChatOllama(model="gpt-oss:latest", temperature=0.0)


def run_pdf_agent(query: str, session_id: str = "default") -> PDFAgentResponse:
    """
    Non-streaming PDF agent execution.

    Args:
        query: User's question
        session_id: Session ID for conversation memory

    Returns:
        PDFAgentResponse with content and metadata
    """
    start_time = time.time()
    memory = SharedMemory.get_session(session_id)
    history = memory.get()  # Get history BEFORE adding current message
    memory.add_user(query)

    try:
        # Retrieve context
        context = retrieve_context(query)

        # Build prompt and invoke LLM (uses module-level singleton)
        prompt = f"""You are a Saudi Grid Code document assistant with access to document context and conversation history.

Document Context:
{context}

Conversation History:
{history}

Current Question: {query}

Instructions:
- For follow-up questions using pronouns (they, it, this, that, these, those, them, who, what),
  FIRST check the Conversation History - your previous answers contain the information needed.
- The Conversation History shows what you already told the user - use it to answer follow-ups like
  "who are they?", "can you explain more?", "what does that mean?", etc.
- Only say "outside my document scope" if the question is TRULY unrelated to both:
  1. The Document Context above, AND
  2. Your previous answers in Conversation History
- NEVER use general knowledge or information not present in the Document Context or Conversation History.
- If asked about topics like geography, history, general facts, or anything completely unrelated, politely decline."""

        response = llm.invoke(prompt)
        answer = response.content
        memory.add_ai(answer)
        elapsed_time = round(time.time() - start_time, 2)

        return PDFAgentResponse(
            content=answer,
            response_time=f"{elapsed_time}s",
            sources=["Saudi Grid Code Documents"]
        )

    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        error_msg = f"**Error:** {str(e)}"
        memory.add_ai(error_msg)

        return PDFAgentResponse(
            content=error_msg,
            response_time=f"{elapsed_time}s",
            sources=["Error"]
        )


def stream_pdf_agent(query: str, session_id: str = "default") -> Generator[str, None, None]:
    """
    Streaming PDF agent with true LLM token streaming.

    SSE Format:
        data: {"content": "...", "phase": "...", "done": false}\n\n
        data: {"content": "", "done": true, "response_time": "...", "sources": [...]}\n\n

    Args:
        query: User's question
        session_id: Session ID for conversation memory

    Yields:
        SSE-formatted strings with real-time tokens
    """
    start_time = time.time()
    memory = SharedMemory.get_session(session_id)
    history = memory.get()  # Get history BEFORE adding current message
    memory.add_user(query)

    try:
        # Phase 1: Retrieval
        yield _sse_message({"content": "Retrieving documents...", "phase": "retrieval", "done": False})

        t1 = time.time()
        print(f"[TIMING] Before retrieve_context: {t1 - start_time:.2f}s from start")

        context = retrieve_context(query)

        t2 = time.time()
        print(f"[TIMING] After retrieve_context: {t2 - t1:.2f}s (retrieval)")

        # Phase 2: True streaming from LLM
        prompt = f"""You are a Saudi Grid Code document assistant with access to document context and conversation history.

Document Context:
{context}

Conversation History:
{history}

Current Question: {query}

Instructions:
- For follow-up questions using pronouns (they, it, this, that, these, those, them, who, what),
  FIRST check the Conversation History - your previous answers contain the information needed.
- The Conversation History shows what you already told the user - use it to answer follow-ups like
  "who are they?", "can you explain more?", "what does that mean?", etc.
- Only say "outside my document scope" if the question is TRULY unrelated to both:
  1. The Document Context above, AND
  2. Your previous answers in Conversation History
- NEVER use general knowledge or information not present in the Document Context or Conversation History.
- If asked about topics like geography, history, general facts, or anything completely unrelated, politely decline."""

        t3 = time.time()
        print(f"[TIMING] Before LLM stream: {t3 - start_time:.2f}s from start")

        full_answer = ""
        first_token = True
        for chunk in llm.stream(prompt):
            if first_token:
                print(f"[TIMING] First token received: {time.time() - t3:.2f}s after LLM start")
                first_token = False
            text = chunk.content
            full_answer += text
            yield _sse_message({"content": text, "phase": "answer", "done": False})

        memory.add_ai(full_answer)

        # Final message with metadata
        elapsed_time = round(time.time() - start_time, 2)
        yield _sse_message({
            "content": "",
            "done": True,
            "response_time": f"{elapsed_time}s",
            "sources": ["Saudi Grid Code Documents"]
        })

    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        error_msg = f"**Error:** {str(e)}"
        memory.add_ai(error_msg)

        yield _sse_message({
            "content": error_msg,
            "done": True,
            "response_time": f"{elapsed_time}s",
            "sources": ["Error"]
        })


def _sse_message(data: dict) -> str:
    """Format data as SSE message."""
    return f"data: {json.dumps(data)}\n\n"

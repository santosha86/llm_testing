from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

llm = OllamaLLM(model="gpt-oss:latest")

prompt = ChatPromptTemplate.from_template("""
You are a reasoning agent.

Conversation History:
{memory}

Context from documents:
{context}

Reasoning Plan:
{plan}

Rules:
- Use ONLY the document context
- If answer is not found, say "Information not found in documents"

Question:
{question}

Answer step by step, then give a final answer.
""")

def reason(context: str, plan: str, question: str, memory: str) -> str:
    return (prompt | llm).invoke({
        "context": context,
        "plan": plan,
        "question": question,
        "memory": memory
    })

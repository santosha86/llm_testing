from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

llm = OllamaLLM(model="gpt-oss:latest")

prompt = ChatPromptTemplate.from_template("""
You are a planning agent.

Break the question into logical steps.
Return a numbered list only.

Question:
{question}
""")

def plan(question: str) -> str:
    return (prompt | llm).invoke({"question": question})

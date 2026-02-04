from agents.planner import plan
from agents.reasoner import reason
from agents.tools import retrieve_context
from agents.memory import SessionMemory

memory = SessionMemory()

print("\n🧠 Agentic RAG started (with session memory)\n")

# while True:
#     question = input("Ask a question (q to quit / clear to reset): ")

#     if question.lower() == "q":
#         break

#     if question.lower() == "clear":
#         memory.clear()
#         print("🧹 Session memory cleared\n")
#         continue

#     memory.add_user(question)

#     print("\n🧠 Planning...")
#     reasoning_plan = plan(question)
#     print(reasoning_plan)

#     print("\n📚 Retrieving context...")
#     context = retrieve_context(question)

#     print("\n🤖 Reasoning...")
#     answer = reason(
#         context=context,
#         plan=reasoning_plan,
#         question=question,
#         memory=memory.get()
#     )

#     memory.add_ai(answer)

#     print("\n✅ Final Answer:\n")
#     print(answer)

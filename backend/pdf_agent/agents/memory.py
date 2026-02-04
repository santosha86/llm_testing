from langchain_core.messages import HumanMessage, AIMessage

class SessionMemory:
    def __init__(self):
        self.history = []

    def add_user(self, text: str):
        self.history.append(HumanMessage(content=text))

    def add_ai(self, text: str):
        self.history.append(AIMessage(content=text))

    def get(self) -> str:
        return "\n".join(
            f"{'User' if i%2==0 else 'AI'}: {m.content}"
            for i, m in enumerate(self.history)
        )

    def clear(self):
        self.history = []

"""
Shared session memory manager for multi-agent workflow.
Provides conversation history that persists across SQL and PDF agents.
Includes TTL-based cleanup and message limits for stability.
"""

import time
import threading
from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage

# Configuration
SESSION_TTL_SECONDS = 3600  # 1 hour
MAX_MESSAGES_PER_SESSION = 50
CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes


class SessionMemory:
    """Per-session conversation memory with TTL tracking."""

    def __init__(self):
        self.history: List = []
        self.last_accessed: float = time.time()
        self.last_route: str = None  # Track last route used for follow-up detection
        self.pending_disambiguation: Dict = None  # Track pending column disambiguation
        self.last_result_context: Dict = None  # Store key values from last query result for follow-up references

    def _update_access_time(self):
        """Update last accessed timestamp."""
        self.last_accessed = time.time()

    def add_user(self, text: str) -> None:
        """Add a user message to history."""
        self._update_access_time()
        self.history.append(HumanMessage(content=text[:10000]))  # Limit message size
        self._trim_history()

    def add_ai(self, text: str) -> None:
        """Add an AI response to history."""
        self._update_access_time()
        self.history.append(AIMessage(content=text[:50000]))  # Limit message size
        self._trim_history()

    def _trim_history(self) -> None:
        """Keep only the last MAX_MESSAGES_PER_SESSION messages."""
        if len(self.history) > MAX_MESSAGES_PER_SESSION:
            self.history = self.history[-MAX_MESSAGES_PER_SESSION:]

    def get(self) -> str:
        """Get formatted conversation history."""
        self._update_access_time()
        if not self.history:
            return ""
        return "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
            for m in self.history
        )

    def get_messages(self) -> List:
        """Get raw message objects."""
        self._update_access_time()
        return self.history

    def clear(self) -> None:
        """Clear conversation history."""
        self.history = []
        self.last_route = None
        self.pending_disambiguation = None
        self.last_result_context = None
        self._update_access_time()

    def set_pending_disambiguation(self, data: Dict) -> None:
        """Store pending disambiguation data (original query + ambiguous term)."""
        self.pending_disambiguation = data
        self._update_access_time()

    def get_pending_disambiguation(self) -> Dict:
        """Get pending disambiguation data."""
        return self.pending_disambiguation

    def clear_pending_disambiguation(self) -> None:
        """Clear pending disambiguation."""
        self.pending_disambiguation = None

    def has_pending_disambiguation(self) -> bool:
        """Check if there's a pending disambiguation."""
        return self.pending_disambiguation is not None

    def set_last_result_context(self, context: Dict) -> None:
        """Store context from last query result for follow-up references."""
        self.last_result_context = context
        self._update_access_time()

    def get_last_result_context(self) -> Dict:
        """Get last result context for follow-up queries."""
        return self.last_result_context

    def get_context_summary(self) -> str:
        """Get a formatted summary of last result context for LLM prompt."""
        if not self.last_result_context:
            return ""

        context = self.last_result_context
        lines = ["## Previous Query Result Context:"]

        if context.get("type") == "single_result":
            # Single row result - show all values
            values = context.get("values", {})
            for col, val in values.items():
                lines.append(f"- {col}: {val}")
        elif context.get("type") == "multi_result":
            # Multi-row result - show count and key values
            count = context.get("count", 0)
            lines.append(f"- Result count: {count} records")
            key_values = context.get("key_values", {})
            for col, vals in key_values.items():
                if isinstance(vals, list):
                    lines.append(f"- {col} (first values): {', '.join(str(v) for v in vals[:3])}")
                else:
                    lines.append(f"- {col}: {vals}")

        return "\n".join(lines) if len(lines) > 1 else ""

    def set_route(self, route: str) -> None:
        """Store the last route used for follow-up detection."""
        self.last_route = route
        self._update_access_time()

    def get_route(self) -> str:
        """Get the last route used."""
        return self.last_route

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return (time.time() - self.last_accessed) > SESSION_TTL_SECONDS


class SharedMemory:
    """Singleton memory manager for all sessions with automatic cleanup."""

    _sessions: Dict[str, SessionMemory] = {}
    _lock = threading.Lock()
    _cleanup_thread: threading.Thread = None
    _running = False

    @classmethod
    def _start_cleanup_thread(cls):
        """Start background cleanup thread if not running."""
        if cls._cleanup_thread is None or not cls._cleanup_thread.is_alive():
            cls._running = True
            cls._cleanup_thread = threading.Thread(target=cls._cleanup_loop, daemon=True)
            cls._cleanup_thread.start()

    @classmethod
    def _cleanup_loop(cls):
        """Background thread that cleans up expired sessions."""
        while cls._running:
            time.sleep(CLEANUP_INTERVAL_SECONDS)
            cls._cleanup_expired_sessions()

    @classmethod
    def _cleanup_expired_sessions(cls):
        """Remove expired sessions."""
        with cls._lock:
            expired = [
                sid for sid, session in cls._sessions.items()
                if session.is_expired()
            ]
            for sid in expired:
                del cls._sessions[sid]
            if expired:
                print(f"[Memory] Cleaned up {len(expired)} expired sessions")

    @classmethod
    def get_session(cls, session_id: str) -> SessionMemory:
        """Get or create a session memory."""
        cls._start_cleanup_thread()
        with cls._lock:
            if session_id not in cls._sessions:
                cls._sessions[session_id] = SessionMemory()
            return cls._sessions[session_id]

    @classmethod
    def clear_session(cls, session_id: str) -> None:
        """Clear a session's history."""
        with cls._lock:
            if session_id in cls._sessions:
                cls._sessions[session_id].clear()

    @classmethod
    def delete_session(cls, session_id: str) -> None:
        """Delete a session entirely."""
        with cls._lock:
            if session_id in cls._sessions:
                del cls._sessions[session_id]

    @classmethod
    def list_sessions(cls) -> List[str]:
        """List all active session IDs."""
        with cls._lock:
            return list(cls._sessions.keys())

    @classmethod
    def get_session_count(cls) -> int:
        """Get the number of active sessions."""
        with cls._lock:
            return len(cls._sessions)

import time
from functools import lru_cache
from ..vector import retriever

# Cache for repeated queries (max 100 queries, based on query text)
@lru_cache(maxsize=100)
def _cached_retrieve(question: str) -> str:
    """Cached retrieval - returns joined document content."""
    docs = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in docs)


def retrieve_context(question: str) -> str:
    """Retrieve context with caching and timing."""
    t1 = time.time()

    # Use cached retrieval
    result = _cached_retrieve(question)

    t2 = time.time()
    print(f"[TIMING] retriever.invoke took: {t2-t1:.2f}s")
    return result


def clear_retrieval_cache():
    """Clear the retrieval cache (call when documents are updated)."""
    _cached_retrieve.cache_clear()
    print("[Cache] Retrieval cache cleared")

"""Retrieval-only interface for the NovaCart knowledge base."""

from __future__ import annotations

from pathlib import Path

from backend.app.vector_store import SearchResult, VectorStore


def retrieve(
    query: str,
    n_results: int = 5,
    persist_directory: Path | None = None,
) -> list[SearchResult]:
    """Return matching knowledge-base chunks without generating an answer."""

    if not query.strip():
        return []
    if n_results <= 0:
        raise ValueError("n_results must be greater than zero")

    with VectorStore(persist_directory=persist_directory) as store:
        return store.search(query, n_results=n_results)

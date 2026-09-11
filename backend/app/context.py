"""Prepare retrieved knowledge-base chunks for future answer generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.retrieval import retrieve
from backend.app.vector_store import SearchResult


@dataclass(frozen=True)
class PreparedContext:
    """Retrieved evidence and its deterministic prompt-ready representation."""

    query: str
    results: list[SearchResult]
    context_text: str
    result_count: int
    has_usable_context: bool


def _format_context(results: list[SearchResult]) -> str:
    """Format results without changing their retrieved text."""

    sections = [
        f"[Source: {result.source} | Chunk: {result.chunk_id}]\n{result.text}"
        for result in results
    ]
    return "\n\n".join(sections)


def prepare_context(
    query: str,
    n_results: int = 5,
    distance_threshold: float | None = None,
    persist_directory: Path | None = None,
) -> PreparedContext:
    """Retrieve and format evidence without generating an answer."""

    if not query.strip():
        return PreparedContext(query, [], "", 0, False)

    retrieved_results = retrieve(
        query,
        n_results=n_results,
        persist_directory=persist_directory,
    )
    if distance_threshold is not None:
        retrieved_results = [
            result
            for result in retrieved_results
            if result.distance <= distance_threshold
        ]

    context_text = _format_context(retrieved_results)
    return PreparedContext(
        query=query,
        results=retrieved_results,
        context_text=context_text,
        result_count=len(retrieved_results),
        has_usable_context=bool(retrieved_results),
    )
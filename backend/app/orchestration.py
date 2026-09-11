"""Coordinate context preparation and deterministic support responses."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from backend.app.context import PreparedContext, prepare_context
from backend.app.support_response import SupportResponse, build_support_response


def run_support_agent(
    query: str,
    *,
    n_results: int = 5,
    distance_threshold: float | None = None,
    persist_directory: Path | None = None,
    should_escalate: bool = False,
    escalation_reason: str | None = None,
    context_builder: Callable[..., PreparedContext] = prepare_context,
    response_builder: Callable[..., SupportResponse] = build_support_response,
) -> SupportResponse:
    """Prepare context, build a response, and return it unchanged."""

    context = context_builder(
        query,
        n_results=n_results,
        distance_threshold=distance_threshold,
        persist_directory=persist_directory,
    )
    return response_builder(
        query,
        context,
        should_escalate=should_escalate,
        escalation_reason=escalation_reason,
    )
"""Deterministic support-response contract for future answer generation."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.context import PreparedContext
from backend.app.vector_store import SearchResult


EMPTY_QUERY_ANSWER = "Please provide more detail about your NovaCart question."
NO_CONTEXT_ANSWER = (
    "No matching NovaCart policy information was found. Please clarify your question."
)
CONTEXT_ONLY_ANSWER = (
    "Relevant NovaCart policy context was found, but answer generation is not enabled yet."
)
ESCALATION_ANSWER = "This request should be reviewed by NovaCart support."
DEFAULT_ESCALATION_REASON = "The request requires review by NovaCart support."


@dataclass(frozen=True)
class SupportResponse:
    """A deterministic response contract ready for a future answer generator."""

    answer: str
    sources: list[SearchResult]
    has_usable_context: bool
    retrieval_confidence: str
    confidence_reason: str
    should_escalate: bool
    escalation_reason: str | None


def build_support_response(
    query: str,
    context: PreparedContext,
    *,
    should_escalate: bool = False,
    escalation_reason: str | None = None,
) -> SupportResponse:
    """Build a deterministic response from prepared retrieval context."""

    if not query.strip():
        return SupportResponse(
            answer=EMPTY_QUERY_ANSWER,
            sources=[],
            has_usable_context=False,
            retrieval_confidence="none",
            confidence_reason="The customer did not provide a usable query.",
            should_escalate=False,
            escalation_reason=None,
        )

    sources = context.results if context.has_usable_context else []
    if should_escalate:
        return SupportResponse(
            answer=ESCALATION_ANSWER,
            sources=sources,
            has_usable_context=context.has_usable_context,
            retrieval_confidence=("medium" if context.has_usable_context else "none"),
            confidence_reason=(
                "Relevant retrieved policy context is available."
                if context.has_usable_context
                else "No usable policy context was retrieved."
            ),
            should_escalate=True,
            escalation_reason=escalation_reason or DEFAULT_ESCALATION_REASON,
        )

    if not context.has_usable_context:
        return SupportResponse(
            answer=NO_CONTEXT_ANSWER,
            sources=[],
            has_usable_context=False,
            retrieval_confidence="none",
            confidence_reason="No usable NovaCart policy context was retrieved.",
            should_escalate=False,
            escalation_reason=None,
        )

    return SupportResponse(
        answer=CONTEXT_ONLY_ANSWER,
        sources=sources,
        has_usable_context=True,
        retrieval_confidence="medium",
        confidence_reason="Relevant retrieved policy context is available.",
        should_escalate=False,
        escalation_reason=None,
    )
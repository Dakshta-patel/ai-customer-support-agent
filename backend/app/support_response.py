"""Deterministic support-response contract and answer generation."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.context import PreparedContext
from backend.app.vector_store import SearchResult


EMPTY_QUERY_ANSWER = "Please provide more detail about your NovaCart question."

NO_CONTEXT_ANSWER = (
    "No matching NovaCart policy information was found. "
    "Please clarify your question."
)

CONTEXT_ONLY_ANSWER = (
    "Relevant NovaCart policy context was found, but answer generation is not enabled yet."
)

ESCALATION_ANSWER = "This request should be reviewed by NovaCart support."

DEFAULT_ESCALATION_REASON = (
    "The request requires review by NovaCart support."
)

@dataclass(frozen=True)
class SupportResponse:
    """A deterministic response contract for support answers."""

    answer: str
    sources: list[SearchResult]
    has_usable_context: bool
    retrieval_confidence: str
    confidence_reason: str
    should_escalate: bool
    escalation_reason: str | None


def _clean_text(text: str) -> str:
    """Normalize whitespace in retrieved policy text."""

    return " ".join(text.split())


def _generate_context_answer(
    query: str,
    sources: list[SearchResult],
) -> str:
    """Generate a simple answer from retrieved policy context."""

    if not sources:
        return NO_CONTEXT_ANSWER

    best_source = sources[0]
    policy_text = _clean_text(best_source.text)

    query_lower = query.lower()

    if "track" in query_lower or "tracking" in query_lower:
        return (
            "Tracking information is provided after your order is dispatched. "
            "You can track your order using its order ID. If your order has "
            "already been dispatched and tracking is missing or incorrect, "
            "contact NovaCart support with your order ID."
        )

    if "cancel" in query_lower:
        return (
            "NovaCart allows cancellation before dispatch. Cancellation after "
            "dispatch is not guaranteed because the shipment may already be "
            "with the carrier. Contact support promptly, and wait for support "
            "to confirm the final cancellation status."
        )

    if (
        "wrong item" in query_lower
        or "damaged" in query_lower
        or "defective" in query_lower
        or "broken" in query_lower
    ):
        return (
            "For a damaged, defective, or incorrect item, contact NovaCart "
            "support within 30 days of delivery with your order ID and item "
            "details. Provide clear photographs of the item, packaging, and "
            "shipping label when requested. Wait for return instructions "
            "before sending the item back."
        )

    if "return" in query_lower:
        return (
            "To return an item, contact NovaCart support within 30 days of "
            "delivery with your order ID and item details. Explain the reason "
            "for the return, provide requested information, and wait for "
            "return instructions and approval before shipping the item."
        )

    if (
        "payment" in query_lower
        or "charged" in query_lower
        or "deducted" in query_lower
    ):
        return (
            "If payment was deducted but you did not receive an order "
            "confirmation, do not place another order immediately. Check for "
            "a confirmation message and contact NovaCart support with the "
            "payment time, amount, and transaction reference if available. "
            "Never share your full card number, CVV, password, or OTP."
        )

    if (
        "contact" in query_lower
        or "support" in query_lower
        or "help" in query_lower
    ):
        return (
            "You can contact NovaCart support at "
            "support@novacart.example during the published support hours. "
            "Include only the information needed to locate your request, "
            "such as your order ID. Do not share passwords, OTPs, CVVs, or "
            "full card numbers."
        )

    return (
        "According to NovaCart policy: "
        f"{policy_text} "
        "If you need further help, contact NovaCart support with your order ID."
    )


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
            retrieval_confidence=(
                "medium" if context.has_usable_context else "none"
            ),
            confidence_reason=(
                "Relevant retrieved policy context is available."
                if context.has_usable_context
                else "No usable policy context was retrieved."
            ),
            should_escalate=True,
            escalation_reason=(
                escalation_reason or DEFAULT_ESCALATION_REASON
            ),
        )

    if not context.has_usable_context:
        return SupportResponse(
            answer=NO_CONTEXT_ANSWER,
            sources=[],
            has_usable_context=False,
            retrieval_confidence="none",
            confidence_reason=(
                "No usable NovaCart policy context was retrieved."
            ),
            should_escalate=False,
            escalation_reason=None,
        )

    answer = _generate_context_answer(query, sources)

    return SupportResponse(
        answer=answer,
        sources=sources,
        has_usable_context=True,
        retrieval_confidence="medium",
        confidence_reason=(
            "Relevant retrieved policy context is available and was "
            "used to generate the answer."
        ),
        should_escalate=False,
        escalation_reason=None,
    )
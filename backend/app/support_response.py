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


def _generate_context_answer(query, sources):
    normalized_query = _clean_text(query).lower()

    if not sources:
        return NO_CONTEXT_ANSWER

    if (
        "where is my order" in normalized_query
        or "track my order" in normalized_query
        or "track order" in normalized_query
        or "tracking" in normalized_query
        or "tracking details" in normalized_query
    ):
        return (
            "Tracking details are provided after dispatch. "
            "Check your order history for tracking information. "
            "If tracking is missing or appears incorrect, contact NovaCart support "
            "with your order ID."
        )

    if (
        "cancel" in normalized_query
        or "cancellation" in normalized_query
    ):
        return (
            "NovaCart allows cancellation before dispatch. "
            "Cancellation after dispatch is not guaranteed because the shipment "
            "may already be with the carrier. Contact support promptly and wait "
            "for support to confirm the final cancellation status."
        )

    if (
        "damaged" in normalized_query
        or "damage" in normalized_query
        or "defective" in normalized_query
        or "defect" in normalized_query
        or "wrong item" in normalized_query
        or "incorrect item" in normalized_query
    ):
        return (
            "Report a damaged, defective, or incorrect item to NovaCart support "
            "as soon as possible. Include your order ID and clear photographs "
            "of the item, packaging, and shipping label when requested. "
            "Do not share passwords, OTPs, CVVs, full card numbers, or unrelated "
            "personal information. Wait for return instructions before sending "
            "the item back."
        )

    if (
        "payment" in normalized_query
        or "charged" in normalized_query
        or "deducted" in normalized_query
        or "debited" in normalized_query
    ):
        return (
            "If payment was deducted but you did not receive an order confirmation, "
            "do not place another order immediately. Check your order history and "
            "email for a delayed confirmation. Contact NovaCart support with the "
            "payment time, amount, and transaction reference if available. "
            "Never share your full card number, CVV, password, or OTP."
        )

    if (
        "return" in normalized_query
        or "refund" in normalized_query
    ):
        return (
            "Check whether your order and item are eligible under NovaCart's "
            "return or refund policy. Contact support with your order ID and "
            "the relevant return or refund status. Do not send the item back "
            "until support provides return instructions."
        )

    if (
        "support" in normalized_query
        or "help" in normalized_query
        or "contact" in normalized_query
    ):
        return (
            "Email support@novacart.example during the published support hours. "
            "Include only the information needed to locate the request, such as "
            "an order ID. Do not share passwords, OTPs, CVVs, or full card numbers."
        )

    best_source = sources[0].text.strip()

    if best_source.startswith("### "):
        best_source = best_source[4:]

    if best_source.startswith("## "):
        best_source = best_source[3:]

    return f"According to NovaCart policy: {best_source}"

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
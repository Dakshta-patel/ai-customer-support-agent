import unittest
from dataclasses import fields

from backend.app.context import PreparedContext
from backend.app.support_response import (
    CONTEXT_ONLY_ANSWER,
    DEFAULT_ESCALATION_REASON,
    EMPTY_QUERY_ANSWER,
    ESCALATION_ANSWER,
    NO_CONTEXT_ANSWER,
    build_support_response,
)
from backend.app.vector_store import SearchResult


def make_result(text: str, source: str, chunk_id: str, distance: float) -> SearchResult:
    return SearchResult(
        text=text,
        source=source,
        chunk_id=chunk_id,
        distance=distance,
    )


def make_context(
    query: str,
    results: list[SearchResult],
    has_usable_context: bool,
) -> PreparedContext:
    return PreparedContext(
        query=query,
        results=results,
        context_text="context",
        result_count=len(results),
        has_usable_context=has_usable_context,
    )


class SupportResponseTests(unittest.TestCase):
    def test_support_response_contract_fields_are_unchanged(self) -> None:
        self.assertEqual(
            [field.name for field in fields(type(make_context("", [], False)))],
            [
                "query",
                "results",
                "context_text",
                "result_count",
                "has_usable_context",
            ],
        )

        response = build_support_response("delivery", make_context("delivery", [], False))
        self.assertEqual(
            [field.name for field in fields(response)],
            [
                "answer",
                "sources",
                "has_usable_context",
                "retrieval_confidence",
                "confidence_reason",
                "should_escalate",
                "escalation_reason",
            ],
        )

    def test_empty_query_fallback(self) -> None:
        context = make_context("", [], False)

        response = build_support_response("   ", context)

        self.assertEqual(response.answer, EMPTY_QUERY_ANSWER)
        self.assertEqual(response.sources, [])
        self.assertFalse(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "none")
        self.assertEqual(response.confidence_reason, "The customer did not provide a usable query.")
        self.assertFalse(response.should_escalate)
        self.assertIsNone(response.escalation_reason)

    def test_no_usable_context_fallback(self) -> None:
        context = make_context("unknown", [], False)

        response = build_support_response("unknown", context)

        self.assertEqual(response.answer, NO_CONTEXT_ANSWER)
        self.assertEqual(response.sources, [])
        self.assertFalse(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "none")
        self.assertFalse(response.should_escalate)

    def test_usable_context_preserves_results_and_order(self) -> None:
        first = make_result("First policy text", "shipping.md", "shipping.md:0", 0.2)
        second = make_result("Second policy text", "returns.md", "returns.md:2", 0.4)
        context = make_context("policy", [first, second], True)

        response = build_support_response("policy", context)

        self.assertNotEqual(response.answer, CONTEXT_ONLY_ANSWER)
        self.assertTrue(response.answer.strip())
        self.assertIs(response.sources[0], first)
        self.assertIs(response.sources[1], second)
        self.assertEqual(response.sources, [first, second])
        self.assertEqual(response.sources[0].source, "shipping.md")
        self.assertEqual(response.sources[0].chunk_id, "shipping.md:0")
        self.assertEqual(response.sources[0].text, "First policy text")
        self.assertEqual(response.sources[0].distance, 0.2)
        self.assertTrue(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "medium")
        self.assertFalse(response.should_escalate)

    def test_explicit_escalation_preserves_sources_and_reason(self) -> None:
        result = make_result("Relevant policy text", "orders.md", "orders.md:1", 0.3)
        context = make_context("cancel my order", [result], True)

        response = build_support_response(
            "cancel my order",
            context,
            should_escalate=True,
            escalation_reason="Cancellation status needs review.",
        )

        self.assertEqual(response.answer, ESCALATION_ANSWER)
        self.assertTrue(response.should_escalate)
        self.assertEqual(response.escalation_reason, "Cancellation status needs review.")
        self.assertEqual(response.sources, [result])
        self.assertTrue(response.has_usable_context)

    def test_escalation_without_reason_uses_default(self) -> None:
        context = make_context("security concern", [], False)

        response = build_support_response(
            "security concern",
            context,
            should_escalate=True,
        )

        self.assertEqual(response.answer, ESCALATION_ANSWER)
        self.assertTrue(response.should_escalate)
        self.assertEqual(response.escalation_reason, DEFAULT_ESCALATION_REASON)
        self.assertFalse(response.has_usable_context)
        self.assertEqual(response.sources, [])

    def test_empty_string_escalation_reason_uses_default(self) -> None:
        context = make_context("security concern", [], False)

        response = build_support_response(
            "security concern",
            context,
            should_escalate=True,
            escalation_reason="",
        )

        self.assertEqual(response.answer, ESCALATION_ANSWER)
        self.assertEqual(response.escalation_reason, DEFAULT_ESCALATION_REASON)

    def test_policy_style_escalation_keeps_reason_structural_and_answer_generic(self) -> None:
        context = make_context("account takeover", [], False)

        response = build_support_response(
            "account takeover",
            context,
            should_escalate=True,
            escalation_reason="The request involves account security or ownership verification.",
        )

        self.assertEqual(response.answer, ESCALATION_ANSWER)
        self.assertNotIn("account_security", response.answer)
        self.assertNotIn("compromise", response.answer)
        self.assertEqual(
            response.escalation_reason,
            "The request involves account security or ownership verification.",
        )

    def test_empty_query_overrides_escalation_request(self) -> None:
        context = make_context("", [], False)

        response = build_support_response(
            " ",
            context,
            should_escalate=True,
            escalation_reason="Explicit test reason",
        )

        self.assertEqual(response.answer, EMPTY_QUERY_ANSWER)
        self.assertFalse(response.should_escalate)
        self.assertIsNone(response.escalation_reason)


if __name__ == "__main__":
    unittest.main()
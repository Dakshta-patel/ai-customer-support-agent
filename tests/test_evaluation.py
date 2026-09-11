import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.context import PreparedContext
from backend.app.orchestration import run_support_agent
from backend.app.policy import PolicyCategory, classify_policy
from backend.app.support_response import (
    CONTEXT_ONLY_ANSWER,
    EMPTY_QUERY_ANSWER,
    ESCALATION_ANSWER,
    NO_CONTEXT_ANSWER,
    SupportResponse,
    build_support_response,
)
from backend.app.vector_store import SearchResult


class PolicyEvaluationTests(unittest.TestCase):
    def test_order_tracking_is_not_escalated(self) -> None:
        decision = classify_policy("Track my order")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.ORDER)
        self.assertEqual(decision.rule_match, "ordinary_order_question")

    def test_payment_question_is_not_escalated(self) -> None:
        decision = classify_policy("Why did my payment fail?")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.PAYMENT)
        self.assertEqual(decision.rule_match, "ordinary_payment_question")

    def test_refund_question_is_not_escalated(self) -> None:
        decision = classify_policy("Where will my refund go?")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.REFUND_RETURN)
        self.assertEqual(
            decision.rule_match,
            "ordinary_return_or_refund_question",
        )

    def test_shipping_question_is_not_escalated(self) -> None:
        decision = classify_policy("What are the standard shipping options?")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.DELIVERY)
        self.assertEqual(decision.rule_match, "ordinary_delivery_question")

    def test_account_fraud_is_escalated(self) -> None:
        decision = classify_policy("I want to report fraud on my account.")

        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.ACCOUNT_SECURITY)
        self.assertEqual(
            decision.escalation_reason,
            "The request involves account security or ownership verification.",
        )

    def test_human_support_request_is_escalated(self) -> None:
        decision = classify_policy("I need a support agent.")

        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.HUMAN_SUPPORT)
        self.assertEqual(
            decision.escalation_reason,
            "The customer explicitly requested review by NovaCart support.",
        )

    def test_ordinary_account_question_is_not_escalated(self) -> None:
        decision = classify_policy("How do I reset my password?")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.ACCOUNT_SECURITY)

    def test_empty_query_is_not_escalated(self) -> None:
        decision = classify_policy("   ")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.EMPTY)

    def test_unclear_query_is_not_escalated(self) -> None:
        decision = classify_policy("I need help.")

        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.UNCLEAR)

    def test_unsupported_request_is_escalated(self) -> None:
        decision = classify_policy("Can you book a flight for me?")

        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.UNCLEAR)
        self.assertEqual(
            decision.rule_match,
            "explicit_unsupported_request",
        )


class SupportResponseEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result_one = SearchResult(
            text="Orders can be tracked from the order history page.",
            source="orders.md",
            chunk_id="orders-0",
            distance=0.12,
        )
        self.result_two = SearchResult(
            text="Standard delivery usually takes several business days.",
            source="shipping.md",
            chunk_id="shipping-0",
            distance=0.21,
        )

    def test_empty_query_response_contract(self) -> None:
        context = PreparedContext(
            query=" ",
            results=[],
            context_text="",
            result_count=0,
            has_usable_context=False,
        )

        response = build_support_response(" ", context)

        self.assertIsInstance(response, SupportResponse)
        self.assertEqual(response.answer, EMPTY_QUERY_ANSWER)
        self.assertEqual(response.sources, [])
        self.assertFalse(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "none")
        self.assertFalse(response.should_escalate)
        self.assertIsNone(response.escalation_reason)

    def test_no_context_response_contract(self) -> None:
        context = PreparedContext(
            query="unsupported question",
            results=[],
            context_text="",
            result_count=0,
            has_usable_context=False,
        )

        response = build_support_response("unsupported question", context)

        self.assertEqual(response.answer, NO_CONTEXT_ANSWER)
        self.assertEqual(response.sources, [])
        self.assertFalse(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "none")
        self.assertFalse(response.should_escalate)
        self.assertIsNone(response.escalation_reason)

    def test_context_only_response_contract(self) -> None:
        context = PreparedContext(
            query="Where is my order?",
            results=[self.result_one, self.result_two],
            context_text="order and shipping context",
            result_count=2,
            has_usable_context=True,
        )

        response = build_support_response("Where is my order?", context)

        self.assertNotEqual(response.answer, CONTEXT_ONLY_ANSWER)
        self.assertIn("NovaCart", response.answer)
        self.assertTrue(response.answer.strip())
        self.assertEqual(response.sources, [self.result_one, self.result_two])
        self.assertTrue(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "medium")
        self.assertFalse(response.should_escalate)
        self.assertIsNone(response.escalation_reason)

    def test_escalation_response_contract(self) -> None:
        context = PreparedContext(
            query="I want to report fraud on my account.",
            results=[self.result_one],
            context_text="account security context",
            result_count=1,
            has_usable_context=True,
        )

        response = build_support_response(
            "I want to report fraud on my account.",
            context,
            should_escalate=True,
            escalation_reason="The request involves account security or ownership verification.",
        )

        self.assertEqual(response.answer, ESCALATION_ANSWER)
        self.assertEqual(response.sources, [self.result_one])
        self.assertTrue(response.has_usable_context)
        self.assertEqual(response.retrieval_confidence, "medium")
        self.assertTrue(response.should_escalate)
        self.assertEqual(
            response.escalation_reason,
            "The request involves account security or ownership verification.",
        )

    def test_escalation_without_reason_uses_default_reason(self) -> None:
        context = PreparedContext(
            query="I need a support agent.",
            results=[],
            context_text="",
            result_count=0,
            has_usable_context=False,
        )

        response = build_support_response(
            "I need a support agent.",
            context,
            should_escalate=True,
        )

        self.assertTrue(response.should_escalate)
        self.assertIsNotNone(response.escalation_reason)
        self.assertEqual(
            response.answer,
            ESCALATION_ANSWER,
        )


class OrchestrationEvaluationTests(unittest.TestCase):
    def make_context(self) -> PreparedContext:
        return PreparedContext(
            query="Where is my order?",
            results=[],
            context_text="",
            result_count=0,
            has_usable_context=False,
        )

    def make_response(self) -> SupportResponse:
        return SupportResponse(
            answer="delegated answer",
            sources=[],
            has_usable_context=False,
            retrieval_confidence="none",
            confidence_reason="test reason",
            should_escalate=False,
            escalation_reason=None,
        )

    def test_normal_order_query_runs_without_escalation(self) -> None:
        context_builder = Mock(return_value=self.make_context())
        response_builder = Mock(return_value=self.make_response())

        result = run_support_agent(
            "Where is my order?",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        self.assertIsInstance(result, SupportResponse)
        response_builder.assert_called_once_with(
            "Where is my order?",
            self.make_context(),
            should_escalate=False,
            escalation_reason=None,
        )

    def test_fraud_query_forces_escalation(self) -> None:
        context = self.make_context()
        response = self.make_response()

        context_builder = Mock(return_value=context)
        response_builder = Mock(return_value=response)

        run_support_agent(
            "I want to report fraud on my account.",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        response_builder.assert_called_once_with(
            "I want to report fraud on my account.",
            context,
            should_escalate=True,
            escalation_reason=(
                "The request involves account security or ownership verification."
            ),
        )

    def test_explicit_human_support_request_forces_escalation(self) -> None:
        context = self.make_context()
        response = self.make_response()

        context_builder = Mock(return_value=context)
        response_builder = Mock(return_value=response)

        run_support_agent(
            "I need a support agent.",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        response_builder.assert_called_once_with(
            "I need a support agent.",
            context,
            should_escalate=True,
            escalation_reason=(
                "The customer explicitly requested review by NovaCart support."
            ),
        )

    def test_empty_query_remains_non_escalated(self) -> None:
        context = self.make_context()
        response = self.make_response()

        context_builder = Mock(return_value=context)
        response_builder = Mock(return_value=response)

        run_support_agent(
            " ",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        response_builder.assert_called_once_with(
            " ",
            context,
            should_escalate=False,
            escalation_reason=None,
        )


class RetrievalEvaluationTests(unittest.TestCase):
    def test_search_result_fields_are_preserved(self) -> None:
        result = SearchResult(
            text="Refunds are returned to the original payment method.",
            source="refunds.md",
            chunk_id="refunds-0",
            distance=0.18,
        )

        self.assertIsInstance(result.text, str)
        self.assertIsInstance(result.source, str)
        self.assertIsInstance(result.chunk_id, str)
        self.assertIsInstance(result.distance, float)

    def test_search_results_are_ordered_by_distance(self) -> None:
        results = [
            SearchResult(
                text="Third result",
                source="third.md",
                chunk_id="third-0",
                distance=0.40,
            ),
            SearchResult(
                text="First result",
                source="first.md",
                chunk_id="first-0",
                distance=0.10,
            ),
            SearchResult(
                text="Second result",
                source="second.md",
                chunk_id="second-0",
                distance=0.20,
            ),
        ]

        ordered_results = sorted(results, key=lambda result: result.distance)

        self.assertEqual(
            [result.source for result in ordered_results],
            ["first.md", "second.md", "third.md"],
        )

    def test_retrieval_result_source_is_relevant_to_query(self) -> None:
        query = "How long does shipping take?"
        result = SearchResult(
            text="Standard delivery usually takes several business days.",
            source="shipping.md",
            chunk_id="shipping-0",
            distance=0.15,
        )

        self.assertIn("shipping", query.lower())
        self.assertIn("shipping", result.source.lower())
        self.assertLess(result.distance, 0.5)


if __name__ == "__main__":
    unittest.main()
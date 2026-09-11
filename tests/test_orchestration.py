import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.context import PreparedContext
from backend.app.orchestration import run_support_agent
from backend.app.policy import PolicyCategory, PolicyDecision
from backend.app.support_response import SupportResponse


class OrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = PreparedContext(
            query="delivery",
            results=[],
            context_text="",
            result_count=0,
            has_usable_context=False,
        )
        self.response = SupportResponse(
            answer="delegated answer",
            sources=[],
            has_usable_context=False,
            retrieval_confidence="none",
            confidence_reason="delegated reason",
            should_escalate=False,
            escalation_reason=None,
        )

    def make_policy_decision(
        self,
        *,
        should_escalate: bool,
        escalation_reason: str | None,
    ) -> PolicyDecision:
        return PolicyDecision(
            should_escalate=should_escalate,
            escalation_reason=escalation_reason,
            policy_category=(
                PolicyCategory.HUMAN_SUPPORT
                if should_escalate
                else PolicyCategory.DELIVERY
            ),
            rule_match="test_rule",
            confidence="high",
        )

    def test_pipeline_calls_each_builder_once_and_returns_exact_response(self) -> None:
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        result = run_support_agent(
            "delivery",
            n_results=3,
            distance_threshold=0.5,
            persist_directory=Path("temporary-store"),
            should_escalate=True,
            escalation_reason="Needs review",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        self.assertIs(result, self.response)
        context_builder.assert_called_once_with(
            "delivery",
            n_results=3,
            distance_threshold=0.5,
            persist_directory=Path("temporary-store"),
        )
        response_builder.assert_called_once_with(
            "delivery",
            self.context,
            should_escalate=True,
            escalation_reason="Needs review",
        )

    def test_policy_escalation_overrides_explicit_false_and_reason(self) -> None:
        policy_decision = self.make_policy_decision(
            should_escalate=True,
            escalation_reason="Policy review required.",
        )
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        with patch(
            "backend.app.orchestration.classify_policy",
            return_value=policy_decision,
        ):
            run_support_agent(
                "security concern",
                should_escalate=False,
                escalation_reason="Caller reason",
                context_builder=context_builder,
                response_builder=response_builder,
            )

        response_builder.assert_called_once_with(
            "security concern",
            self.context,
            should_escalate=True,
            escalation_reason="Policy review required.",
        )

    def test_explicit_escalation_and_reason_are_preserved(self) -> None:
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        with patch(
            "backend.app.orchestration.classify_policy",
            return_value=self.make_policy_decision(
                should_escalate=False,
                escalation_reason=None,
            ),
        ):
            run_support_agent(
                "delivery",
                should_escalate=True,
                escalation_reason="Caller reason",
                context_builder=context_builder,
                response_builder=response_builder,
            )

        response_builder.assert_called_once_with(
            "delivery",
            self.context,
            should_escalate=True,
            escalation_reason="Caller reason",
        )

    def test_policy_classifier_receives_query_and_runs_before_context(self) -> None:
        call_order: list[str] = []
        context_builder = Mock(
            side_effect=lambda *args, **kwargs: (
                call_order.append("context") or self.context
            )
        )
        response_builder = Mock(return_value=self.response)

        policy_classifier = Mock(
            side_effect=lambda query: (
                call_order.append("policy")
                or self.make_policy_decision(
                    should_escalate=False,
                    escalation_reason=None,
                )
            )
        )
        with patch(
            "backend.app.orchestration.classify_policy",
            new=policy_classifier,
        ):
            run_support_agent(
                "Original query",
                context_builder=context_builder,
                response_builder=response_builder,
            )

        policy_classifier.assert_called_once_with("Original query")
        self.assertEqual(call_order, ["policy", "context"])

    def test_context_arguments_and_response_context_remain_unchanged(self) -> None:
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)
        store_path = Path("temporary-store")

        with patch(
            "backend.app.orchestration.classify_policy",
            return_value=self.make_policy_decision(
                should_escalate=False,
                escalation_reason=None,
            ),
        ):
            run_support_agent(
                "delivery",
                n_results=3,
                distance_threshold=0.5,
                persist_directory=store_path,
                context_builder=context_builder,
                response_builder=response_builder,
            )

        context_builder.assert_called_once_with(
            "delivery",
            n_results=3,
            distance_threshold=0.5,
            persist_directory=store_path,
        )
        response_builder.assert_called_once_with(
            "delivery",
            self.context,
            should_escalate=False,
            escalation_reason=None,
        )

    def test_default_values_are_forwarded(self) -> None:
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        run_support_agent(
            "delivery",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        context_builder.assert_called_once_with(
            "delivery",
            n_results=5,
            distance_threshold=None,
            persist_directory=None,
        )
        response_builder.assert_called_once_with(
            "delivery",
            self.context,
            should_escalate=False,
            escalation_reason=None,
        )

    def test_empty_query_behavior_is_delegated(self) -> None:
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        result = run_support_agent(
            " ",
            context_builder=context_builder,
            response_builder=response_builder,
        )

        self.assertIs(result, self.response)
        context_builder.assert_called_once()
        response_builder.assert_called_once_with(
            " ",
            self.context,
            should_escalate=False,
            escalation_reason=None,
        )

    def test_empty_query_classification_does_not_change_compatibility(self) -> None:
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        policy_classifier = Mock(
            return_value=self.make_policy_decision(
                should_escalate=False,
                escalation_reason=None,
            )
        )
        with patch(
            "backend.app.orchestration.classify_policy",
            new=policy_classifier,
        ):
            run_support_agent(
                " ",
                context_builder=context_builder,
                response_builder=response_builder,
            )

        policy_classifier.assert_called_once_with(" ")
        response_builder.assert_called_once_with(
            " ",
            self.context,
            should_escalate=False,
            escalation_reason=None,
        )

    def test_policy_classification_exception_propagates(self) -> None:
        error = RuntimeError("policy failure")
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(return_value=self.response)

        policy_classifier = Mock(side_effect=error)
        with patch(
            "backend.app.orchestration.classify_policy",
            new=policy_classifier,
        ):
            with self.assertRaises(RuntimeError) as raised:
                run_support_agent(
                    "delivery",
                    context_builder=context_builder,
                    response_builder=response_builder,
                )

        self.assertIs(raised.exception, error)
        context_builder.assert_not_called()
        response_builder.assert_not_called()

    def test_context_builder_exception_propagates(self) -> None:
        error = RuntimeError("context failure")
        context_builder = Mock(side_effect=error)
        response_builder = Mock(return_value=self.response)

        with self.assertRaises(RuntimeError) as raised:
            run_support_agent(
                "delivery",
                context_builder=context_builder,
                response_builder=response_builder,
            )

        self.assertIs(raised.exception, error)
        response_builder.assert_not_called()

    def test_response_builder_exception_propagates(self) -> None:
        error = RuntimeError("response failure")
        context_builder = Mock(return_value=self.context)
        response_builder = Mock(side_effect=error)

        with self.assertRaises(RuntimeError) as raised:
            run_support_agent(
                "delivery",
                context_builder=context_builder,
                response_builder=response_builder,
            )

        self.assertIs(raised.exception, error)
        context_builder.assert_called_once()


if __name__ == "__main__":
    unittest.main()
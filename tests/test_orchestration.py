import unittest
from pathlib import Path
from unittest.mock import Mock

from backend.app.context import PreparedContext
from backend.app.orchestration import run_support_agent
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
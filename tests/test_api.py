import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.support_response import SupportResponse
from backend.app.vector_store import SearchResult


def make_response(
    *,
    answer: str = "Test answer",
    sources: list[SearchResult] | None = None,
    has_usable_context: bool = True,
    should_escalate: bool = False,
    escalation_reason: str | None = None,
) -> SupportResponse:
    return SupportResponse(
        answer=answer,
        sources=sources or [],
        has_usable_context=has_usable_context,
        retrieval_confidence="medium" if has_usable_context else "none",
        confidence_reason="Test confidence reason",
        should_escalate=should_escalate,
        escalation_reason=escalation_reason,
    )


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_route_is_unchanged(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "AI Customer Support Agent backend is running."},
        )

    def test_health_route_is_unchanged(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_support_accepts_query_and_passes_it_unchanged(self) -> None:
        response_value = make_response()
        with patch(
            "backend.app.main.run_support_agent",
            return_value=response_value,
        ) as run_agent:
            response = self.client.post("/support", json={"query": "  delivery?  "})

        self.assertEqual(response.status_code, 200)
        run_agent.assert_called_once_with("  delivery?  ")
        self.assertEqual(response.json()["answer"], "Test answer")

    def test_support_serializes_sources_in_order(self) -> None:
        sources = [
            SearchResult("First text", "shipping.md", "shipping.md:0", 0.2),
            SearchResult("Second text", "returns.md", "returns.md:2", 0.4),
        ]
        with patch(
            "backend.app.main.run_support_agent",
            return_value=make_response(sources=sources),
        ):
            response = self.client.post("/support", json={"query": "policy"})

        self.assertEqual(
            response.json()["sources"],
            [
                {
                    "text": "First text",
                    "source": "shipping.md",
                    "chunk_id": "shipping.md:0",
                    "distance": 0.2,
                },
                {
                    "text": "Second text",
                    "source": "returns.md",
                    "chunk_id": "returns.md:2",
                    "distance": 0.4,
                },
            ],
        )

    def test_support_serializes_escalation_reason_as_null(self) -> None:
        with patch(
            "backend.app.main.run_support_agent",
            return_value=make_response(
                has_usable_context=False,
                should_escalate=False,
                escalation_reason=None,
            ),
        ):
            response = self.client.post("/support", json={"query": "unknown"})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["escalation_reason"])

    def test_empty_and_whitespace_queries_are_delegated(self) -> None:
        with patch(
            "backend.app.main.run_support_agent",
            return_value=make_response(
                answer="Please provide more detail",
                has_usable_context=False,
            ),
        ) as run_agent:
            empty_response = self.client.post("/support", json={"query": ""})
            whitespace_response = self.client.post("/support", json={"query": " \t"})

        self.assertEqual(empty_response.status_code, 200)
        self.assertEqual(whitespace_response.status_code, 200)
        self.assertEqual(run_agent.call_args_list[0].args, ("",))
        self.assertEqual(run_agent.call_args_list[1].args, (" \t",))

    def test_missing_query_returns_unprocessable_entity(self) -> None:
        response = self.client.post("/support", json={})

        self.assertEqual(response.status_code, 422)

    def test_malformed_body_returns_unprocessable_entity(self) -> None:
        response = self.client.post(
            "/support",
            content="{not valid json}",
            headers={"content-type": "application/json"},
        )

        self.assertEqual(response.status_code, 422)

    def test_orchestration_exception_is_not_silently_converted(self) -> None:
        error = RuntimeError("orchestration failure")
        with patch(
            "backend.app.main.run_support_agent",
            Mock(side_effect=error),
        ):
            with self.assertRaises(RuntimeError) as raised:
                self.client.post("/support", json={"query": "delivery"})

        self.assertIs(raised.exception, error)


if __name__ == "__main__":
    unittest.main()
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.context import prepare_context
from backend.app.vector_store import SearchResult


def make_result(
    text: str, source: str, chunk_id: str, distance: float
) -> SearchResult:
    return SearchResult(
        text=text,
        source=source,
        chunk_id=chunk_id,
        distance=distance,
    )


class ContextPreparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.store_path = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_reuses_retrieval_and_passes_arguments(self) -> None:
        results = [make_result("Delivery policy", "shipping.md", "shipping.md:0", 0.2)]
        with patch("backend.app.context.retrieve", return_value=results) as mock_retrieve:
            prepared = prepare_context(
                "delivery",
                n_results=3,
                distance_threshold=0.5,
                persist_directory=self.store_path,
            )

        mock_retrieve.assert_called_once_with(
            "delivery",
            n_results=3,
            persist_directory=self.store_path,
        )
        self.assertEqual(prepared.results, results)

    def test_empty_query_skips_retrieval_and_returns_empty_context(self) -> None:
        with patch("backend.app.context.retrieve") as mock_retrieve:
            prepared = prepare_context("  ", persist_directory=self.store_path)

        mock_retrieve.assert_not_called()
        self.assertEqual(prepared.results, [])
        self.assertEqual(prepared.context_text, "")
        self.assertEqual(prepared.result_count, 0)
        self.assertFalse(prepared.has_usable_context)

    def test_no_results_returns_empty_context(self) -> None:
        with patch("backend.app.context.retrieve", return_value=[]):
            prepared = prepare_context("unknown", persist_directory=self.store_path)

        self.assertEqual(prepared.context_text, "")
        self.assertEqual(prepared.result_count, 0)
        self.assertFalse(prepared.has_usable_context)

    def test_preserves_order_text_and_identifiers(self) -> None:
        first = make_result("First exact text", "shipping.md", "shipping.md:0", 0.1)
        second = make_result("Second exact text", "returns.md", "returns.md:2", 0.3)
        with patch("backend.app.context.retrieve", return_value=[first, second]):
            prepared = prepare_context("policy", persist_directory=self.store_path)

        self.assertEqual(prepared.results, [first, second])
        self.assertEqual(
            prepared.context_text,
            "[Source: shipping.md | Chunk: shipping.md:0]\n"
            "First exact text\n\n"
            "[Source: returns.md | Chunk: returns.md:2]\n"
            "Second exact text",
        )
        self.assertIn("shipping.md", prepared.context_text)
        self.assertIn("shipping.md:0", prepared.context_text)
        self.assertIn("returns.md", prepared.context_text)
        self.assertIn("returns.md:2", prepared.context_text)

    def test_distance_threshold_filters_results(self) -> None:
        close = make_result("Keep this", "shipping.md", "shipping.md:0", 0.2)
        far = make_result("Drop this", "returns.md", "returns.md:2", 0.8)
        with patch("backend.app.context.retrieve", return_value=[close, far]):
            prepared = prepare_context(
                "policy",
                distance_threshold=0.5,
                persist_directory=self.store_path,
            )

        self.assertEqual(prepared.results, [close])
        self.assertEqual(prepared.result_count, 1)
        self.assertTrue(prepared.has_usable_context)
        self.assertNotIn("Drop this", prepared.context_text)

    def test_all_results_filtered_out_produces_unusable_context(self) -> None:
        result = make_result("Too far", "shipping.md", "shipping.md:0", 0.8)
        with patch("backend.app.context.retrieve", return_value=[result]):
            prepared = prepare_context(
                "policy",
                distance_threshold=0.5,
                persist_directory=self.store_path,
            )

        self.assertEqual(prepared.results, [])
        self.assertEqual(prepared.context_text, "")
        self.assertEqual(prepared.result_count, 0)
        self.assertFalse(prepared.has_usable_context)

    def test_shipping_and_returns_queries_preserve_sources(self) -> None:
        shipping = make_result("Shipping policy", "shipping.md", "shipping.md:0", 0.1)
        returns = make_result("Returns policy", "returns.md", "returns.md:0", 0.1)
        with patch(
            "backend.app.context.retrieve",
            side_effect=[[shipping], [returns]],
        ):
            shipping_context = prepare_context("delivery", persist_directory=self.store_path)
            returns_context = prepare_context("return", persist_directory=self.store_path)

        self.assertIn("shipping.md", shipping_context.context_text)
        self.assertIn("returns.md", returns_context.context_text)
        self.assertEqual(shipping_context.result_count, 1)
        self.assertEqual(returns_context.result_count, 1)

    def test_invalid_result_count_follows_retrieval_validation(self) -> None:
        with patch(
            "backend.app.context.retrieve",
            side_effect=ValueError("n_results must be greater than zero"),
        ):
            with self.assertRaises(ValueError):
                prepare_context("shipping", n_results=0, persist_directory=self.store_path)


if __name__ == "__main__":
    unittest.main()
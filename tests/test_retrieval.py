import tempfile
import unittest
from pathlib import Path

from backend.app.retrieval import retrieve
from backend.app.vector_store import VectorStore


class RetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.store_path = Path(self.temporary_directory.name)
        with VectorStore(persist_directory=self.store_path) as store:
            store.index_chunks()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_delivery_query_retrieves_shipping_source(self) -> None:
        results = retrieve(
            "How long does standard delivery take?",
            n_results=3,
            persist_directory=self.store_path,
        )

        self.assertTrue(results)
        self.assertTrue(any(result.source == "shipping.md" for result in results))

    def test_return_query_retrieves_returns_source(self) -> None:
        results = retrieve(
            "How do I return a damaged product?",
            n_results=3,
            persist_directory=self.store_path,
        )

        self.assertTrue(results)
        self.assertTrue(any(result.source == "returns.md" for result in results))

    def test_results_preserve_search_result_fields_and_types(self) -> None:
        results = retrieve(
            "What is the return window?",
            n_results=2,
            persist_directory=self.store_path,
        )

        self.assertTrue(results)
        for result in results:
            self.assertIsInstance(result.text, str)
            self.assertIsInstance(result.source, str)
            self.assertIsInstance(result.chunk_id, str)
            self.assertIsInstance(result.distance, float)

    def test_empty_query_returns_no_results(self) -> None:
        self.assertEqual(
            retrieve("   ", persist_directory=self.store_path),
            [],
        )

    def test_non_positive_result_count_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            retrieve("shipping", n_results=0, persist_directory=self.store_path)
        with self.assertRaises(ValueError):
            retrieve("shipping", n_results=-1, persist_directory=self.store_path)

    def test_real_vector_store_directory_is_not_used(self) -> None:
        self.assertNotEqual(self.store_path, Path("data/vector_store").resolve())


if __name__ == "__main__":
    unittest.main()

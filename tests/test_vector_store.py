import tempfile
import unittest
from pathlib import Path

from backend.app.vector_store import VectorStore


class VectorStoreTests(unittest.TestCase):
    def test_indexing_is_persistent_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store_path = Path(temporary_directory)
            with VectorStore(persist_directory=store_path) as store:
                first_count = store.index_chunks()
                second_count = store.index_chunks()

                self.assertEqual(first_count, 88)
                self.assertEqual(second_count, first_count)
                self.assertEqual(store.collection.count(), first_count)

            with VectorStore(persist_directory=store_path) as reopened_store:
                self.assertEqual(reopened_store.collection.count(), first_count)

    def test_delivery_query_retrieves_shipping_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with VectorStore(persist_directory=Path(temporary_directory)) as store:
                store.index_chunks()

                results = store.search("How long does standard delivery take?", n_results=3)

                self.assertTrue(results)
                self.assertTrue(any(result.source == "shipping.md" for result in results))
                self.assertTrue(all(result.text and result.source and result.chunk_id for result in results))

    def test_return_query_retrieves_returns_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with VectorStore(persist_directory=Path(temporary_directory)) as store:
                store.index_chunks()

                results = store.search("How do I return a damaged product?", n_results=3)

                self.assertTrue(results)
                self.assertTrue(any(result.source == "returns.md" for result in results))
                self.assertTrue(all(result.distance >= 0 for result in results))


if __name__ == "__main__":
    unittest.main()
import unittest

from backend.app.knowledge_base import load_documents, load_knowledge_base


class KnowledgeBaseLoadingTests(unittest.TestCase):
    def test_loads_all_documents_and_creates_metadata_rich_chunks(self) -> None:
        documents = load_documents()
        chunks = load_knowledge_base()

        self.assertEqual(len(documents), 7)
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(chunk.text.strip() for chunk in chunks))
        self.assertTrue(all(chunk.source in documents for chunk in chunks))
        self.assertTrue(all(chunk.chunk_id for chunk in chunks))
        self.assertEqual({chunk.source for chunk in chunks}, set(documents))

        loaded_text = "\n".join(chunk.text for chunk in chunks)
        self.assertIn("3-5 business days", loaded_text)
        self.assertIn("5-7 business days", loaded_text)
        self.assertIn("cancellation refund", loaded_text)


if __name__ == "__main__":
    unittest.main()

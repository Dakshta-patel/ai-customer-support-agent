"""Create and search a persistent local vector index for NovaCart chunks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from backend.app.knowledge_base import KnowledgeChunk, load_knowledge_base


COLLECTION_NAME = "novacart_knowledge_base"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class SearchResult:
    """A knowledge-base match returned by similarity search."""

    text: str
    source: str
    chunk_id: str
    distance: float


def get_vector_store_directory() -> Path:
    """Return the project-root-relative directory used for persistent storage."""

    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "vector_store"


class VectorStore:
    """Build and query a local Chroma collection using sentence embeddings."""

    def __init__(
        self,
        persist_directory: Path | None = None,
        model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        storage_path = persist_directory or get_vector_store_directory()
        storage_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(storage_path))
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        self.model = SentenceTransformer(model_name, device="cpu")

    def close(self) -> None:
        """Release Chroma resources, including persistent file handles."""

        self.client.close()

    def __enter__(self) -> "VectorStore":
        return self

    def __exit__(self, exception_type: object, exception: object, traceback: object) -> None:
        self.close()

    def index_chunks(self, chunks: list[KnowledgeChunk] | None = None) -> int:
        """Insert or update all knowledge chunks and return the indexed count."""

        chunks = chunks if chunks is not None else load_knowledge_base()
        if not chunks:
            return 0

        texts = [chunk.text for chunk in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "source": chunk.source,
                    "chunk_id": chunk.chunk_id,
                    "index": str(chunk.index),
                }
                for chunk in chunks
            ],
        )
        return len(chunks)

    def search(self, query: str, n_results: int = 5) -> list[SearchResult]:
        """Return the nearest indexed chunks for a natural-language query."""

        if not query.strip():
            return []

        result = self.collection.query(
            query_embeddings=[self.model.encode(query, normalize_embeddings=True).tolist()],
            n_results=min(n_results, self.collection.count()),
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            SearchResult(
                text=text,
                source=metadata["source"],
                chunk_id=metadata["chunk_id"],
                distance=distance,
            )
            for text, metadata, distance in zip(documents, metadatas, distances)
        ]


def build_index(persist_directory: Path | None = None) -> int:
    """Build or update the default persistent index and return its chunk count."""

    with VectorStore(persist_directory=persist_directory) as store:
        return store.index_chunks()


def similarity_search(
    query: str, n_results: int = 5, persist_directory: Path | None = None
) -> list[SearchResult]:
    """Search the default persistent index for the closest knowledge chunks."""

    with VectorStore(persist_directory=persist_directory) as store:
        return store.search(query, n_results)
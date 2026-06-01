from __future__ import annotations

from app.knowledge.embeddings import GeminiEmbeddingClient
from app.knowledge.models import SearchResult
from app.knowledge.vector_store import PostgresVectorStore


class KnowledgeRetriever:
    def __init__(self, embedder: GeminiEmbeddingClient, store: PostgresVectorStore) -> None:
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: str, limit: int = 3) -> list[SearchResult]:
        embedding = self.embedder.embed_text(query)
        return self.store.search(embedding, limit=limit)


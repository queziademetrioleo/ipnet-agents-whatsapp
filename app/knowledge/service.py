from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.config import AppConfig
from app.knowledge.chunking import chunk_document
from app.knowledge.embeddings import GeminiEmbeddingClient
from app.knowledge.models import KnowledgeDocument, SearchResult
from app.knowledge.retriever import KnowledgeRetriever
from app.knowledge.vector_store import PostgresVectorStore


class KnowledgeService:
    def __init__(
        self,
        enabled: bool,
        store: PostgresVectorStore | None = None,
        retriever: KnowledgeRetriever | None = None,
    ) -> None:
        self.enabled = enabled
        self.store = store
        self.retriever = retriever

    def ingest_text(
        self,
        title: str,
        content: str,
        source_uri: str,
        document_id: str | None = None,
    ) -> int:
        self._assert_ready()
        doc = KnowledgeDocument(
            document_id=document_id or str(uuid4()),
            title=title,
            source_uri=source_uri,
            content=content,
        )
        chunks = chunk_document(doc)
        if not chunks:
            return 0

        assert self.retriever is not None
        assert self.store is not None
        embeddings = self.retriever.embedder.embed_texts([chunk.content for chunk in chunks])
        self.store.ensure_schema()
        self.store.upsert_document(doc, chunks, embeddings)
        return len(chunks)

    def ingest_file(self, path: Path) -> int:
        content = path.read_text(encoding="utf-8")
        return self.ingest_text(
            title=path.stem,
            content=content,
            source_uri=str(path),
            document_id=path.stem,
        )

    def search(self, query: str, limit: int = 3) -> list[SearchResult]:
        self._assert_ready()
        assert self.retriever is not None
        assert self.store is not None
        self.store.ensure_schema()
        return self.retriever.retrieve(query, limit=limit)

    def search_as_text(self, query: str, limit: int = 3) -> str:
        if not self.enabled:
            return "Base de conhecimento nao configurada para este ambiente."

        try:
            results = self.search(query, limit=limit)
        except Exception as exc:
            return f"Falha ao consultar a base de conhecimento: {exc}"

        if not results:
            return "Nenhum trecho relevante foi encontrado na base de conhecimento."

        parts: list[str] = []
        for result in results:
            parts.append(
                f"Fonte: {result.title}\n"
                f"Relevancia: {result.score:.3f}\n"
                f"Trecho: {result.content}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def is_misconfigured_response(text: str) -> bool:
        prefixes = (
            "Base de conhecimento nao configurada",
            "Falha ao consultar a base de conhecimento:",
            "Nenhum trecho relevante foi encontrado",
        )
        return text.startswith(prefixes)

    def _assert_ready(self) -> None:
        if not self.enabled or self.store is None or self.retriever is None:
            raise RuntimeError("Base de conhecimento nao configurada para este ambiente.")


def build_knowledge_service(config: AppConfig) -> KnowledgeService:
    if not config.knowledge_enabled or not config.gemini_api_key or not config.postgres_url:
        return KnowledgeService(enabled=False)

    store = PostgresVectorStore(
        dsn=config.postgres_sync_url,
        schema=config.knowledge_schema,
        dimensions=config.embedding_dimensions,
    )
    embedder = GeminiEmbeddingClient(
        api_key=config.gemini_api_key,
        model=config.embedding_model,
        output_dimensions=config.embedding_dimensions,
    )
    retriever = KnowledgeRetriever(embedder=embedder, store=store)
    return KnowledgeService(enabled=True, store=store, retriever=retriever)

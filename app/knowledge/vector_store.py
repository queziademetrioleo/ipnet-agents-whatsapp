from __future__ import annotations

import json
from typing import Iterable

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from app.knowledge.models import DocumentChunk, KnowledgeDocument, SearchResult


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


class PostgresVectorStore:
    def __init__(self, dsn: str, schema: str, dimensions: int) -> None:
        self.dsn = dsn
        self.schema = schema
        self.dimensions = dimensions

    def ensure_schema(self) -> None:
        dim_sql = sql.SQL(str(self.dimensions))
        schema_sql = sql.Identifier(self.schema)

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(schema_sql))
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.documents (
                            document_id TEXT PRIMARY KEY,
                            title TEXT NOT NULL,
                            source_uri TEXT NOT NULL,
                            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    ).format(schema_sql)
                )
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.chunks (
                            document_id TEXT NOT NULL REFERENCES {}.documents(document_id) ON DELETE CASCADE,
                            chunk_index INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                            embedding vector({}) NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            PRIMARY KEY (document_id, chunk_index)
                        )
                        """
                    ).format(schema_sql, schema_sql, dim_sql)
                )
                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS knowledge_chunks_document_idx
                        ON {}.chunks (document_id)
                        """
                    ).format(schema_sql)
                )
                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx
                        ON {}.chunks
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                        """
                    ).format(schema_sql)
                )
            conn.commit()

    def upsert_document(
        self,
        document: KnowledgeDocument,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks e embeddings precisam ter o mesmo tamanho.")

        schema_sql = sql.Identifier(self.schema)

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.documents (document_id, title, source_uri, metadata, updated_at)
                        VALUES (%s, %s, %s, %s::jsonb, NOW())
                        ON CONFLICT (document_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            source_uri = EXCLUDED.source_uri,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW()
                        """
                    ).format(schema_sql),
                    (
                        document.document_id,
                        document.title,
                        document.source_uri,
                        json.dumps(document.metadata, ensure_ascii=False),
                    ),
                )
                cur.execute(
                    sql.SQL("DELETE FROM {}.chunks WHERE document_id = %s").format(schema_sql),
                    (document.document_id,),
                )
                for chunk, embedding in zip(chunks, embeddings):
                    cur.execute(
                        sql.SQL(
                            """
                            INSERT INTO {}.chunks (
                                document_id,
                                chunk_index,
                                content,
                                metadata,
                                embedding,
                                updated_at
                            )
                            VALUES (%s, %s, %s, %s::jsonb, %s::vector, NOW())
                            """
                        ).format(schema_sql),
                        (
                            chunk.document_id,
                            chunk.chunk_index,
                            chunk.content,
                            json.dumps(chunk.metadata, ensure_ascii=False),
                            _vector_literal(embedding),
                        ),
                    )
            conn.commit()

    def search(self, query_embedding: list[float], limit: int = 3) -> list[SearchResult]:
        schema_sql = sql.Identifier(self.schema)
        vector = _vector_literal(query_embedding)

        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        SELECT
                            c.document_id,
                            d.title,
                            d.source_uri,
                            c.chunk_index,
                            c.content,
                            c.metadata,
                            1 - (c.embedding <=> %s::vector) AS score
                        FROM {}.chunks c
                        INNER JOIN {}.documents d
                            ON d.document_id = c.document_id
                        ORDER BY c.embedding <=> %s::vector
                        LIMIT %s
                        """
                    ).format(schema_sql, schema_sql),
                    (vector, vector, limit),
                )
                rows = cur.fetchall()

        return [
            SearchResult(
                document_id=row["document_id"],
                title=row["title"],
                source_uri=row["source_uri"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                score=float(row["score"]),
                metadata=row["metadata"] or {},
            )
            for row in rows
        ]

    def count_chunks(self) -> int:
        schema_sql = sql.Identifier(self.schema)
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}.chunks").format(schema_sql))
                row = cur.fetchone()
        return int(row[0]) if row else 0


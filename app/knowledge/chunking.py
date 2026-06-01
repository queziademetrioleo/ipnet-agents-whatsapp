from __future__ import annotations

from app.knowledge.models import DocumentChunk, KnowledgeDocument


def chunk_document(
    document: KnowledgeDocument,
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> list[DocumentChunk]:
    text = " ".join(document.content.split())
    if not text:
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            split_at = text.rfind(" ", start, end)
            if split_at > start + 200:
                end = split_at

        chunk_text = text[start:end].strip()
        if chunk_text:
            metadata = dict(document.metadata)
            metadata.update(
                {
                    "title": document.title,
                    "source_uri": document.source_uri,
                    "chunk_index": chunk_index,
                }
            )
            chunks.append(
                DocumentChunk(
                    document_id=document.document_id,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    metadata=metadata,
                )
            )

        if end >= len(text):
            break

        start = max(0, end - overlap_chars)
        chunk_index += 1

    return chunks


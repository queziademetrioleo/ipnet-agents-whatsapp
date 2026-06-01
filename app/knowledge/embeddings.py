from __future__ import annotations

from typing import Any

from google import genai


class GeminiEmbeddingClient:
    def __init__(self, api_key: str, model: str, output_dimensions: int) -> None:
        self.api_key = api_key
        self.model = model
        self.output_dimensions = output_dimensions
        self._client = genai.Client(api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.models.embed_content(
            model=self.model,
            contents=texts,
            config={"output_dimensionality": self.output_dimensions},
        )
        embeddings = self._coerce_embeddings(response)

        if len(embeddings) != len(texts):
            raise ValueError(
                "Quantidade de embeddings retornada nao bate com a quantidade de textos enviados."
            )
        return embeddings

    def embed_text(self, text: str) -> list[float]:
        embeddings = self.embed_texts([text])
        return embeddings[0]

    @staticmethod
    def _coerce_embeddings(response: Any) -> list[list[float]]:
        raw_embeddings = getattr(response, "embeddings", None)
        if raw_embeddings is None:
            single_embedding = getattr(response, "embedding", None)
            if single_embedding is None:
                raise ValueError("Resposta de embedding sem campo de embeddings.")
            raw_embeddings = [single_embedding]

        embeddings: list[list[float]] = []
        for item in raw_embeddings:
            values = getattr(item, "values", None)
            if values is None and isinstance(item, dict):
                values = item.get("values")
            if values is None:
                raise ValueError("Embedding retornado sem vetor de valores.")
            embeddings.append([float(value) for value in values])
        return embeddings


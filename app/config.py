from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AppConfig:
    agent_name: str
    gemini_api_key: str
    postgres_url: str
    embedding_model: str
    embedding_dimensions: int
    knowledge_enabled: bool
    knowledge_schema: str
    knowledge_top_k: int
    lead_schema: str

    @property
    def postgres_sync_url(self) -> str:
        return self.postgres_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            agent_name=os.getenv("IPNET_AGENT_NAME", "IPNET WhatsApp Agent"),
            gemini_api_key=os.getenv("IPNET_GEMINI_API_KEY", ""),
            postgres_url=os.getenv("IPNET_POSTGRES_URL", ""),
            embedding_model=os.getenv("IPNET_EMBEDDING_MODEL", "gemini-embedding-001"),
            embedding_dimensions=int(os.getenv("IPNET_EMBEDDING_DIMENSIONS", "768")),
            knowledge_enabled=_env_bool("IPNET_KNOWLEDGE_ENABLED", True),
            knowledge_schema=os.getenv("IPNET_KNOWLEDGE_SCHEMA", "knowledge"),
            knowledge_top_k=int(os.getenv("IPNET_KNOWLEDGE_TOP_K", "3")),
            lead_schema=os.getenv("IPNET_LEAD_SCHEMA", "ipnet_agent"),
        )


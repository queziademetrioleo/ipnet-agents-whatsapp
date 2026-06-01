from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IPNET_", env_file=".env", extra="ignore")

    gemini_api_key: str = Field(..., description="Google Gemini API Key")
    gemini_model: str = Field("gemini-2.5-flash", description="Modelo Gemini a usar")
    gemini_temperature: float = Field(0.7, ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(2048, gt=0)

    evolution_api_url: str = Field(..., description="URL base da Evolution API")
    evolution_api_key: str = Field(..., description="API Key da Evolution API")
    instance_name: str = Field(..., description="Nome da instancia WhatsApp na Evolution API")

    postgres_url: str = Field(..., description="PostgreSQL connection string")
    redis_url: str = Field(..., description="Redis URL")

    debounce_seconds: float = Field(5.0, ge=0.5, le=30.0)
    max_history_messages: int = Field(20, ge=1)
    session_ttl_seconds: int = Field(3600, ge=60)

    host: str = Field("0.0.0.0")
    port: int = Field(8080, ge=1, le=65535)
    webhook_secret: str | None = Field(None)

    @field_validator("evolution_api_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


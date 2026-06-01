"""
Classe principal WhatsAppAgent.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Any, Callable

from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.postgres import PostgresStorage
from fastapi import FastAPI
import uvicorn

from whatsapp_agent_ipnet.config import AgentConfig
from whatsapp_agent_ipnet.debouncer import BufferedMessage, MessageDebouncer
from whatsapp_agent_ipnet.evolution import EvolutionClient
from whatsapp_agent_ipnet.memory.history import ConversationHistory
from whatsapp_agent_ipnet.memory.session import SessionMemory
from whatsapp_agent_ipnet.webhook import create_webhook_router

logger = logging.getLogger(__name__)


class WhatsAppAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        gemini_api_key: str,
        evolution_api_url: str,
        evolution_api_key: str,
        instance_name: str,
        postgres_url: str,
        redis_url: str,
        debounce_seconds: float = 5.0,
        gemini_model: str = "gemini-2.5-flash",
        gemini_temperature: float = 0.7,
        gemini_max_tokens: int = 2048,
        max_history_messages: int = 20,
        session_ttl_seconds: int = 3600,
        webhook_secret: str | None = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.host = host
        self.port = port
        self._config = AgentConfig(
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            gemini_temperature=gemini_temperature,
            gemini_max_tokens=gemini_max_tokens,
            evolution_api_url=evolution_api_url,
            evolution_api_key=evolution_api_key,
            instance_name=instance_name,
            postgres_url=postgres_url,
            redis_url=redis_url,
            debounce_seconds=debounce_seconds,
            max_history_messages=max_history_messages,
            session_ttl_seconds=session_ttl_seconds,
            webhook_secret=webhook_secret,
            host=host,
            port=port,
        )
        self._tools: list[Callable] = []
        self._extra_instructions: list[str] = []
        self._on_qrcode: Callable | None = None
        self._on_connection: Callable | None = None
        self._evolution: EvolutionClient | None = None
        self._session_memory: SessionMemory | None = None
        self._history: ConversationHistory | None = None
        self._debouncer: MessageDebouncer | None = None
        self._agno_agent: Agent | None = None
        self._app: FastAPI | None = None

    @classmethod
    def from_config(cls, name: str, system_prompt: str, config: AgentConfig) -> "WhatsAppAgent":
        return cls(name=name, system_prompt=system_prompt, **config.model_dump())

    @classmethod
    def from_env(cls, name: str, system_prompt: str) -> "WhatsAppAgent":
        return cls.from_config(name, system_prompt, AgentConfig())  # type: ignore[call-arg]

    def tool(self, fn: Callable) -> Callable:
        if not callable(fn):
            raise TypeError(f"@agent.tool espera uma função, recebeu {type(fn)}")
        self._tools.append(fn)
        return fn

    def add_instruction(self, instruction: str) -> None:
        self._extra_instructions.append(instruction)

    def on_qrcode(self, fn: Callable) -> Callable:
        self._on_qrcode = fn
        return fn

    def on_connection_change(self, fn: Callable) -> Callable:
        self._on_connection = fn
        return fn

    def start(self, webhook_url: str | None = None) -> None:
        self._webhook_url_override = webhook_url
        uvicorn.run(self._create_app(), host=self.host, port=self.port, log_level="info")

    def get_app(self, webhook_url: str | None = None) -> FastAPI:
        self._webhook_url_override = webhook_url
        return self._create_app()

    def _create_app(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self._startup()
            yield
            await self._shutdown()

        app = FastAPI(title=f"{self.name} — WhatsApp Agent", version="0.1.0", lifespan=lifespan)
        app.state.agent = self
        self._app = app
        return app

    async def _startup(self) -> None:
        cfg = self._config
        logger.info("Iniciando %s...", self.name)
        self._evolution = EvolutionClient(cfg.evolution_api_url, cfg.evolution_api_key)
        await self._evolution.connect()

        self._session_memory = SessionMemory(redis_url=cfg.redis_url, ttl_seconds=cfg.session_ttl_seconds)
        await self._session_memory.connect()

        self._history = ConversationHistory(postgres_url=cfg.postgres_url, max_messages=cfg.max_history_messages)
        await self._history.setup()

        self._agno_agent = self._build_agno_agent()
        self._debouncer = MessageDebouncer(debounce_seconds=cfg.debounce_seconds, callback=self._on_messages_ready)

        if self._app is not None:
            self._app.include_router(
                create_webhook_router(
                    debouncer=self._debouncer,
                    webhook_secret=cfg.webhook_secret,
                    on_qrcode=self._on_qrcode,
                    on_connection_change=self._on_connection,
                )
            )
        logger.info("%s pronto na porta %d", self.name, cfg.port)

    async def _shutdown(self) -> None:
        if self._debouncer:
            await self._debouncer.flush_all()
        if self._evolution:
            await self._evolution.disconnect()
        if self._session_memory:
            await self._session_memory.disconnect()
        if self._history:
            await self._history.teardown()

    def _build_agno_agent(self) -> Agent:
        cfg = self._config
        system = self.system_prompt
        if self._extra_instructions:
            system += "\n\n" + "\n".join(f"- {instruction}" for instruction in self._extra_instructions)
        storage = PostgresStorage(
            db_url=cfg.postgres_url.replace("postgresql+asyncpg://", "postgresql://"),
            table_name="ipnet_agno_sessions",
        )
        return Agent(
            name=self.name,
            model=Gemini(id=cfg.gemini_model, api_key=cfg.gemini_api_key),
            instructions=system,
            tools=self._tools or None,
            storage=storage,
            add_history_to_messages=True,
            num_history_responses=cfg.max_history_messages,
            markdown=False,
        )

    async def _on_messages_ready(self, phone: str, messages: list[BufferedMessage]) -> None:
        assert self._evolution is not None
        assert self._session_memory is not None
        assert self._history is not None
        assert self._agno_agent is not None

        if not await self._session_memory.acquire_lock(phone, ttl=60):
            logger.warning("Mensagem de %s ignorada — já está sendo processada", phone)
            return

        try:
            await self._session_memory.set_processing(phone)
            user_text = "\n".join(message.text for message in messages)
            logger.info("Processando mensagem de %s: %s", phone, user_text[:100])
            await self._history.add_user(phone, user_text)

            try:
                await self._evolution.send_typing(
                    self._config.instance_name,
                    phone,
                    duration_ms=int(self._config.debounce_seconds * 1000),
                )
            except Exception:
                pass

            response = await asyncio.to_thread(self._agno_agent.run, user_text, session_id=phone)
            response_text = self._extract_response_text(response)
            if not response_text:
                logger.warning("Agente retornou resposta vazia para %s", phone)
                return

            await self._history.add_assistant(phone, response_text)
            for chunk in self._split_message(response_text):
                await self._evolution.send_text(
                    self._config.instance_name,
                    phone,
                    chunk,
                    quoted_message_id=messages[-1].message_id or None,
                )
                if len(chunk) > 500:
                    await asyncio.sleep(0.5)
        except Exception:
            logger.exception("Erro ao processar mensagem de %s", phone)
            try:
                await self._evolution.send_text(
                    self._config.instance_name,
                    phone,
                    "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente em instantes.",
                )
            except Exception:
                pass
        finally:
            await self._session_memory.set_active(phone)
            await self._session_memory.release_lock(phone)

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        if isinstance(response, str):
            return response.strip()
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                return " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                ).strip()
        return str(response).strip()

    @staticmethod
    def _split_message(text: str, max_len: int = 4000) -> list[str]:
        if len(text) <= max_len:
            return [text]

        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for paragraph in text.split("\n\n"):
            paragraph_len = len(paragraph) + 2
            if current_len + paragraph_len > max_len and current:
                chunks.append("\n\n".join(current))
                current = [paragraph]
                current_len = paragraph_len
            else:
                current.append(paragraph)
                current_len += paragraph_len
        if current:
            chunks.append("\n\n".join(current))
        return chunks or [text]

    async def send_message(self, phone: str, text: str) -> None:
        if self._evolution is None:
            raise RuntimeError("Agente não iniciado.")
        await self._evolution.send_text(self._config.instance_name, phone, text)

    async def clear_history(self, phone: str) -> None:
        if self._history:
            await self._history.clear(phone)
        if self._session_memory:
            await self._session_memory.delete(phone)


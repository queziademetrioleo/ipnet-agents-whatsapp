"""
Debouncer de mensagens WhatsApp.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class BufferedMessage:
    phone: str
    text: str
    message_id: str
    timestamp: float = field(default_factory=time.monotonic)


MessageCallback = Callable[[str, list[BufferedMessage]], Awaitable[None]]
MEDIA_TYPES = frozenset({"image", "audio", "video", "document", "sticker", "ptt"})


class MessageDebouncer:
    def __init__(
        self,
        debounce_seconds: float,
        callback: MessageCallback,
        max_buffer_size: int = 20,
    ) -> None:
        self.debounce_seconds = debounce_seconds
        self.callback = callback
        self.max_buffer_size = max_buffer_size
        self._buffers: dict[str, list[BufferedMessage]] = {}
        self._timers: dict[str, asyncio.TimerHandle] = {}
        self._lock = asyncio.Lock()

    async def add(
        self,
        phone: str,
        text: str,
        message_id: str = "",
        message_type: str = "text",
    ) -> None:
        msg = BufferedMessage(phone=phone, text=text, message_id=message_id)

        if message_type in MEDIA_TYPES:
            await self._flush_immediate(phone, msg)
            return

        async with self._lock:
            if phone not in self._buffers:
                self._buffers[phone] = []

            buf = self._buffers[phone]
            if len(buf) >= self.max_buffer_size:
                logger.warning("Buffer cheio para %s (%d msgs) — processando agora", phone, len(buf))
                self._cancel_timer(phone)
                await self._fire(phone)

            self._buffers.setdefault(phone, []).append(msg)
            self._reschedule_timer(phone)

    async def flush(self, phone: str) -> None:
        async with self._lock:
            self._cancel_timer(phone)
            if self._buffers.get(phone):
                await self._fire(phone)

    async def flush_all(self) -> None:
        for phone in list(self._buffers.keys()):
            await self.flush(phone)

    def _reschedule_timer(self, phone: str) -> None:
        self._cancel_timer(phone)
        loop = asyncio.get_event_loop()
        self._timers[phone] = loop.call_later(
            self.debounce_seconds,
            lambda: asyncio.ensure_future(self._timer_fire(phone)),
        )

    def _cancel_timer(self, phone: str) -> None:
        timer = self._timers.pop(phone, None)
        if timer:
            timer.cancel()

    async def _timer_fire(self, phone: str) -> None:
        async with self._lock:
            await self._fire(phone)

    async def _fire(self, phone: str) -> None:
        messages = self._buffers.pop(phone, [])
        self._timers.pop(phone, None)
        if not messages:
            return
        try:
            await self.callback(phone, messages)
        except Exception:
            logger.exception("Erro no callback do debouncer para %s", phone)

    async def _flush_immediate(self, phone: str, media_msg: BufferedMessage) -> None:
        async with self._lock:
            self._cancel_timer(phone)
            pending = self._buffers.pop(phone, [])

        if pending:
            try:
                await self.callback(phone, pending)
            except Exception:
                logger.exception("Erro no flush de texto pendente para %s", phone)

        try:
            await self.callback(phone, [media_msg])
        except Exception:
            logger.exception("Erro no callback de mídia para %s", phone)

    @property
    def pending_phones(self) -> list[str]:
        return list(self._buffers.keys())

    def buffer_size(self, phone: str) -> int:
        return len(self._buffers.get(phone, []))


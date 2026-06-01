"""
Servidor de webhook FastAPI para receber eventos da Evolution API.
"""

from __future__ import annotations

import hmac
import logging
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from pydantic import BaseModel, Field

from whatsapp_agent_ipnet.debouncer import MessageDebouncer

logger = logging.getLogger(__name__)


class EvolutionWebhookPayload(BaseModel):
    event: str
    instance: str
    data: dict[str, Any] = Field(default_factory=dict)
    destination: str = ""
    date_time: str = ""
    server_url: str = ""
    apikey: str = ""


QRCodeCallback = Callable[[str, str], Awaitable[None]]
ConnectionCallback = Callable[[str, str], Awaitable[None]]


def create_webhook_router(
    debouncer: MessageDebouncer,
    webhook_secret: str | None = None,
    on_qrcode: QRCodeCallback | None = None,
    on_connection_change: ConnectionCallback | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/webhook", tags=["webhook"])

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/{instance_name}")
    async def receive_event(
        instance_name: str,
        request: Request,
        background: BackgroundTasks,
    ) -> Response:
        if webhook_secret:
            incoming_secret = request.headers.get("x-webhook-secret", "")
            if not hmac.compare_digest(incoming_secret, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook secret")

        body = await request.json()
        payload = EvolutionWebhookPayload.model_validate(body)
        logger.debug("Webhook recebido: event=%s instance=%s", payload.event, payload.instance)

        match payload.event:
            case "messages.upsert":
                background.add_task(_handle_message, payload, debouncer)
            case "qrcode.updated":
                background.add_task(_handle_qrcode, payload, on_qrcode)
            case "connection.update":
                background.add_task(_handle_connection, payload, on_connection_change)
            case _:
                logger.debug("Evento ignorado: %s", payload.event)

        return Response(status_code=200)

    return router


async def _handle_message(payload: EvolutionWebhookPayload, debouncer: MessageDebouncer) -> None:
    data = payload.data
    key = data.get("key", {})
    if key.get("fromMe", False):
        return

    remote_jid: str = key.get("remoteJid", "")
    if not remote_jid or "status@broadcast" in remote_jid:
        return

    phone = remote_jid.split("@")[0]
    message_id: str = key.get("id", "")
    message_type: str = data.get("messageType", "conversation")
    msg_content = data.get("message", {}) or {}
    text = _extract_text(msg_content, message_type)
    if not text:
        logger.debug("Mensagem sem texto extraível de %s (tipo: %s)", phone, message_type)
        return

    logger.info("Mensagem de %s [%s]: %s", phone, message_type, text[:80])
    await debouncer.add(
        phone=phone,
        text=text,
        message_id=message_id,
        message_type=_normalize_type(message_type),
    )


async def _handle_qrcode(payload: EvolutionWebhookPayload, callback: QRCodeCallback | None) -> None:
    qr_data = payload.data.get("qrcode", {})
    base64_qr = qr_data.get("base64", "") if isinstance(qr_data, dict) else str(qr_data)
    logger.info("Novo QR code para instância %s", payload.instance)
    if callback:
        await callback(payload.instance, base64_qr)


async def _handle_connection(
    payload: EvolutionWebhookPayload,
    callback: ConnectionCallback | None,
) -> None:
    state = payload.data.get("state", "unknown")
    logger.info("Conexão da instância %s mudou para: %s", payload.instance, state)
    if callback:
        await callback(payload.instance, state)


def _extract_text(message: dict[str, Any], message_type: str) -> str:
    if text := message.get("conversation"):
        return text
    if ext := message.get("extendedTextMessage"):
        return ext.get("text", "")
    for media_key in ("imageMessage", "videoMessage", "documentMessage"):
        if media := message.get(media_key):
            caption = media.get("caption", "")
            if caption:
                return f"[{media_key.replace('Message', '')}] {caption}"
            return f"[{media_key.replace('Message', '')}]"
    if message.get("audioMessage") or message.get("pttMessage"):
        return "[Áudio]"
    if message.get("stickerMessage"):
        return "[Sticker]"
    return ""


_TYPE_MAP = {
    "conversation": "text",
    "extendedTextMessage": "text",
    "imageMessage": "image",
    "audioMessage": "audio",
    "videoMessage": "video",
    "documentMessage": "document",
    "stickerMessage": "sticker",
    "pttMessage": "ptt",
}


def _normalize_type(raw: str) -> str:
    return _TYPE_MAP.get(raw, "text")


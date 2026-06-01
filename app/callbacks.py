from __future__ import annotations

from whatsapp_agent_ipnet import WhatsAppAgent


def register_callbacks(agent: WhatsAppAgent) -> None:
    @agent.on_qrcode
    async def handle_qrcode(instance_name: str, base64_qr: str) -> None:
        print(f"[qrcode] Novo QR code disponivel para {instance_name}.")

    @agent.on_connection_change
    async def handle_connection_change(instance_name: str, state: str) -> None:
        print(f"[connection] {instance_name}: {state}")


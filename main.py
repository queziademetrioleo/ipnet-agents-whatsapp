from pathlib import Path
import os

from whatsapp_agent_ipnet import WhatsAppAgent

from tools import register_tools


def load_system_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    return prompt_path.read_text(encoding="utf-8").strip()


agent = WhatsAppAgent.from_env(
    name=os.getenv("IPNET_AGENT_NAME", "IPNET WhatsApp Agent"),
    system_prompt=load_system_prompt(),
)

register_tools(agent)


@agent.on_qrcode
async def handle_qrcode(instance_name: str, base64_qr: str) -> None:
    print(f"[qrcode] Novo QR code disponivel para {instance_name}.")


@agent.on_connection_change
async def handle_connection_change(instance_name: str, state: str) -> None:
    print(f"[connection] {instance_name}: {state}")


if __name__ == "__main__":
    agent.start()

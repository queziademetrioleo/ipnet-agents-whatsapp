from pathlib import Path
import os

from app.tools import register_tools
from whatsapp_agent_ipnet import WhatsAppAgent


def load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system_prompt.md"
    return prompt_path.read_text(encoding="utf-8").strip()


agent = WhatsAppAgent.from_env(
    name=os.getenv("IPNET_AGENT_NAME", "IPNET WhatsApp Agent"),
    system_prompt=load_system_prompt(),
)

register_tools(agent)
agent.add_instruction(
    "Antes de responder perguntas factuais sobre operacao, seguranca, bateria, camera ou "
    "manutencao de drone, consulte primeiro a ferramenta consultar_base_conhecimento."
)
agent.add_instruction(
    "Quando a duvida nao puder ser resolvida com seguranca ou exigir suporte humano, "
    "registre o caso com a ferramenta registrar_suporte_drone."
)


@agent.on_qrcode
async def handle_qrcode(instance_name: str, base64_qr: str) -> None:
    print(f"[qrcode] Novo QR code disponivel para {instance_name}.")


@agent.on_connection_change
async def handle_connection_change(instance_name: str, state: str) -> None:
    print(f"[connection] {instance_name}: {state}")


if __name__ == "__main__":
    agent.start()

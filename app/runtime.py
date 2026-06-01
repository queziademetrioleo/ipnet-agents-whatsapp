from __future__ import annotations

from pathlib import Path

from whatsapp_agent_ipnet import WhatsAppAgent

from app.callbacks import register_callbacks
from app.config import AppConfig
from app.tools import register_tools


def load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"
    return prompt_path.read_text(encoding="utf-8").strip()


def create_agent() -> WhatsAppAgent:
    config = AppConfig.from_env()
    agent = WhatsAppAgent.from_env(
        name=config.agent_name,
        system_prompt=load_system_prompt(),
    )
    register_tools(agent)
    register_callbacks(agent)
    agent.add_instruction(
        "Antes de responder perguntas factuais sobre produtos, processos, politicas ou "
        "conteudo interno, consulte primeiro a ferramenta consultar_base_conhecimento."
    )
    agent.add_instruction(
        "Quando o usuario pedir contato humano, proposta, demonstracao ou retorno comercial, "
        "registre o lead com a ferramenta registrar_interesse."
    )
    return agent


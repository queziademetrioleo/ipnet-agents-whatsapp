"""
Pacote local do runtime do agente WhatsApp da IPNET.
"""

from __future__ import annotations

__version__ = "0.1.2-local"
__all__ = ["WhatsAppAgent", "AgentConfig", "EvolutionClient"]


def __getattr__(name: str):
    if name == "WhatsAppAgent":
        from whatsapp_agent_ipnet.agent import WhatsAppAgent
        return WhatsAppAgent
    if name == "AgentConfig":
        from whatsapp_agent_ipnet.config import AgentConfig
        return AgentConfig
    if name == "EvolutionClient":
        from whatsapp_agent_ipnet.evolution import EvolutionClient
        return EvolutionClient
    raise AttributeError(f"module 'whatsapp_agent_ipnet' has no attribute {name!r}")


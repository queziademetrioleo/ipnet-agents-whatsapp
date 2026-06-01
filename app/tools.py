from __future__ import annotations

from whatsapp_agent_ipnet import WhatsAppAgent

from app.config import AppConfig
from app.knowledge.service import build_knowledge_service
from app.services.leads import build_lead_capture_service

_FAQ_FALLBACK = {
    "bateria": "Antes do voo, confirme carga acima de 50%, ausencia de estufamento e encaixe firme da bateria.",
    "calibr": "A calibracao so deve ser feita em superficie nivelada e longe de estruturas metalicas ou campos magneticos fortes.",
    "sinal": "Se houver perda de sinal, mantenha a calma, aguarde o retorno automatico configurado e evite novos comandos bruscos.",
    "camera": "Para imagem tremida, verifique limpeza da lente, status do gimbal e se o drone concluiu a inicializacao completa.",
    "pre-voo": "O checklist pre-voo inclui bateria, hellices, GPS, area livre, clima e ponto de retorno configurado.",
}


def _fallback_faq(pergunta: str) -> str:
    pergunta_lower = pergunta.lower()
    for keyword, answer in _FAQ_FALLBACK.items():
        if keyword in pergunta_lower:
            return answer
    return "Nao encontrei uma resposta segura no FAQ. Posso registrar seus dados para retorno."


def register_tools(agent: WhatsAppAgent) -> None:
    config = AppConfig.from_env()
    knowledge = build_knowledge_service(config)
    leads = build_lead_capture_service(config)

    @agent.tool
    def consultar_checklist_pre_voo() -> str:
        """Retorna um checklist pre-voo para operacao segura do drone."""
        return (
            "Checklist pre-voo:\n"
            "1. Confirme bateria do drone e do controle acima de 50%.\n"
            "2. Verifique hellices sem trinca, empeno ou folga.\n"
            "3. Ligue controle, drone e aplicativo na ordem recomendada pelo fabricante.\n"
            "4. Aguarde GPS e ponto de retorno estarem confirmados.\n"
            "5. Inspecione a area para pessoas, fios, arvores e obstaculos.\n"
            "6. Confirme clima, vento e visibilidade adequados.\n"
            "7. Faça decolagem inicial curta para validar estabilidade."
        )

    @agent.tool
    def orientar_manutencao_basica() -> str:
        """Explica cuidados basicos de limpeza, armazenamento e manutencao preventiva do drone."""
        return (
            "Manutencao basica recomendada:\n"
            "1. Limpe casco, sensores e lente com pano macio e seco.\n"
            "2. Remova poeira e residuos das hellices apos o voo.\n"
            "3. Armazene baterias em local seco, ventilado e sem calor excessivo.\n"
            "4. Evite guardar a bateria totalmente carregada por longos periodos.\n"
            "5. Verifique folga em motores, trem de pouso e gimbal.\n"
            "6. Atualize firmware apenas com bateria suficiente e conexao estavel."
        )

    @agent.tool
    def consultar_base_conhecimento(pergunta: str) -> str:
        """
        Busca respostas na base de conhecimento vetorial do agente.
        Use antes de responder perguntas factuais sobre produto, processo, politica ou operacao.
        """
        return knowledge.search_as_text(pergunta, limit=config.knowledge_top_k)

    @agent.tool
    def consultar_faq(pergunta: str) -> str:
        """Busca respostas curtas para perguntas frequentes sobre uso, seguranca e operacao de drone."""
        resposta = knowledge.search_as_text(pergunta, limit=config.knowledge_top_k)
        if not knowledge.is_misconfigured_response(resposta):
            return resposta
        return _fallback_faq(pergunta)

    @agent.tool
    def registrar_suporte_drone(
        nome: str,
        email: str,
        assunto: str,
        modelo_drone: str = "",
        telefone: str = "",
        observacoes: str = "",
    ) -> str:
        """
        Registra um caso para suporte humano quando a duvida nao puder ser resolvida no chat
        ou quando houver risco de dano, falha persistente ou comportamento anormal do drone.
        """
        notas = observacoes
        if modelo_drone:
            prefix = f"Modelo do drone: {modelo_drone}."
            notas = f"{prefix} {observacoes}".strip()
        try:
            lead = leads.capture_interest(
                name=nome,
                email=email,
                phone=telefone,
                subject=assunto,
                notes=notas,
            )
        except Exception as exc:
            return f"Nao consegui registrar o suporte agora. Registre manualmente e informe este erro: {exc}"
        primeiro_nome = nome.split()[0] if nome.strip() else "cliente"
        return (
            f"Perfeito, {primeiro_nome}. Registrei seu caso no protocolo {lead.lead_id} "
            f"e o suporte humano vai retornar pelo email {email}."
        )

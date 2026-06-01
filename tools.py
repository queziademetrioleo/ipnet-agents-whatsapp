from whatsapp_agent_ipnet import WhatsAppAgent


def register_tools(agent: WhatsAppAgent) -> None:
    @agent.tool
    def listar_planos() -> str:
        """Lista os planos atualmente disponiveis com preco resumido."""
        return (
            "Planos disponiveis:\n"
            "- Basic: R$ 99/mes\n"
            "- Pro: R$ 199/mes\n"
            "- Enterprise: sob consulta"
        )

    @agent.tool
    def consultar_faq(pergunta: str) -> str:
        """Busca respostas curtas para perguntas frequentes sobre contratacao e suporte."""
        faq = {
            "teste": "Oferecemos um periodo de teste assistido. Posso registrar seu interesse.",
            "pagamento": "Aceitamos PIX, boleto e cartao, conforme a politica comercial vigente.",
            "suporte": "O suporte comercial funciona em horario comercial. Posso coletar seus dados para retorno.",
            "cancelamento": "As regras de cancelamento dependem do plano contratado. Posso registrar seu caso.",
        }
        pergunta_lower = pergunta.lower()
        for keyword, answer in faq.items():
            if keyword in pergunta_lower:
                return answer
        return "Nao encontrei uma resposta segura no FAQ. Posso registrar seus dados para retorno."

    @agent.tool
    def registrar_interesse(nome: str, email: str, assunto: str) -> str:
        """
        Registra o interesse do cliente para retorno comercial ou operacional.
        Use quando o cliente pedir proposta, demonstracao, contato humano ou follow-up.
        """
        print(f"[lead] nome={nome} email={email} assunto={assunto}")
        return (
            f"Perfeito, {nome.split()[0]}. "
            f"Registrei seu interesse em '{assunto}' e vamos retornar pelo email {email}."
        )

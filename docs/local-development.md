# Desenvolvimento local

Este documento cobre o setup local minimo para editar prompt, tools e validar o agente antes do deploy.

## 1. Pre-requisitos

- Python 3.11+
- Docker
- acesso a Gemini API
- acesso a Evolution API

## 2. Instalar dependencias do projeto

```bash
cp .env.example .env
make setup
```

## 3. Subir PostgreSQL e Redis locais

```bash
make infra-up
```

O `compose.yaml` deste repo sobe:

- PostgreSQL em `127.0.0.1:5432`
- Redis em `127.0.0.1:6379`

## 4. Preencher o `.env`

Exemplo local:

```env
IPNET_AGENT_NAME=IPNET WhatsApp Agent
IPNET_INSTANCE_NAME=ipnet-whatsapp-agent
IPNET_GEMINI_API_KEY=AIza...
IPNET_EVOLUTION_API_URL=https://evolution.seudominio.com
IPNET_EVOLUTION_API_KEY=sua-chave
IPNET_POSTGRES_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agentdb
IPNET_REDIS_URL=redis://127.0.0.1:6379/0
IPNET_HOST=0.0.0.0
IPNET_PORT=8080
```

## 5. O que editar

- `prompts/system_prompt.md`: tom, comportamento e regras do agente
- `app/tools.py`: integracoes, FAQ, registro de lead, consultas
- `app/knowledge/`: chunking, embeddings e busca vetorial

## 6. Subir o agente

```bash
make run
```

## 7. Validacoes locais

Healthcheck:

```bash
make health
```

QR code:

```bash
make qrcode
```

Status da instancia:

```bash
make status
```

## 8. O que o runtime cria automaticamente

Na primeira inicializacao com PostgreSQL valido, o runtime deste repo cria automaticamente:

- `ipnet_conversation_history`
- `ipnet_agno_sessions`

## 9. Quando usar Cloud SQL localmente

Se voce quiser desenvolver mais perto de producao, pode usar Cloud SQL local com proxy e manter Redis local ou externo.

Nessa situacao, a URL do Postgres continua com `127.0.0.1`, porque o proxy escuta localmente.

## 10. Erros comuns

### O agente sobe, mas falha ao processar mensagens

Normalmente e um destes pontos:

- `IPNET_POSTGRES_URL` invalida
- `IPNET_REDIS_URL` invalida
- Gemini API key incorreta
- Evolution API URL ou API key incorretas

### `make qrcode` nao retorna nada

Verifique:

- a instancia existe na Evolution API
- a chave da Evolution API esta correta
- a instancia nao esta ja conectada

## 11. Encerrar a infraestrutura local

```bash
make infra-down
```

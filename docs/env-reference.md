# Environment Reference

Referencia das variaveis `IPNET_*` usadas por este projeto.

## Identidade do agente

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_AGENT_NAME` | sim | `IPNET WhatsApp Agent` | Nome amigavel do agente |
| `IPNET_INSTANCE_NAME` | sim | `ipnet-whatsapp-agent` | Nome da instancia usada na Evolution API e no webhook |

## Gemini

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_GEMINI_API_KEY` | sim | `AIza...` | Chave da API Gemini |
| `IPNET_GEMINI_MODEL` | nao | `gemini-2.5-flash` | Modelo padrao do agente |
| `IPNET_GEMINI_TEMPERATURE` | nao | `0.7` | Criatividade das respostas |
| `IPNET_GEMINI_MAX_TOKENS` | nao | `2048` | Limite de tokens de resposta |

## Evolution API

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_EVOLUTION_API_URL` | sim | `https://evolution.seudominio.com` | URL base da Evolution API |
| `IPNET_EVOLUTION_API_KEY` | sim | `sua-chave` | API key da Evolution |

## Persistencia

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_POSTGRES_URL` | sim | `postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agentdb` | URL do PostgreSQL |
| `IPNET_REDIS_URL` | sim | `redis://127.0.0.1:6379/0` | URL do Redis |

## Knowledge Base

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_KNOWLEDGE_ENABLED` | nao | `true` | Liga ou desliga a base vetorial |
| `IPNET_KNOWLEDGE_SCHEMA` | nao | `knowledge` | Schema onde ficam documentos e chunks |
| `IPNET_KNOWLEDGE_TOP_K` | nao | `3` | Quantidade padrao de trechos retornados |
| `IPNET_EMBEDDING_MODEL` | nao | `gemini-embedding-001` | Modelo usado para embeddings |
| `IPNET_EMBEDDING_DIMENSIONS` | nao | `768` | Dimensao do vetor salvo no Postgres |

## Persistencia de negocio

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_LEAD_SCHEMA` | nao | `ipnet_agent` | Schema onde os leads capturados sao persistidos |

## Runtime

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_DEBOUNCE_SECONDS` | nao | `5` | Espera antes de consolidar mensagens |
| `IPNET_MAX_HISTORY_MESSAGES` | nao | `20` | Quantidade maxima de mensagens recuperadas do historico |
| `IPNET_SESSION_TTL_SECONDS` | nao | `3600` | TTL das sessoes no Redis |
| `IPNET_WEBHOOK_SECRET` | nao | `um-secret-longo` | Segredo opcional para validar o webhook |
| `IPNET_HOST` | nao | `0.0.0.0` | Host local do servidor |
| `IPNET_PORT` | nao | `8080` | Porta local do servidor |

## Deploy

| Variavel | Obrigatoria | Exemplo | Finalidade |
|---|---|---|---|
| `IPNET_SERVICE_ACCOUNT` | depende | `runtime-sa@projeto.iam.gserviceaccount.com` | SA usada no Cloud Run |

## Ambientes recomendados

### Desenvolvimento local

```env
IPNET_POSTGRES_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agentdb
IPNET_REDIS_URL=redis://127.0.0.1:6379/0
```

### Cloud Run

```env
IPNET_POSTGRES_URL=postgresql+asyncpg://agentuser:SENHA@127.0.0.1:5432/agentdb
IPNET_REDIS_URL=redis://10.x.x.x:6379/0
IPNET_SERVICE_ACCOUNT=sua-sa@SEU_PROJECT_ID.iam.gserviceaccount.com
```

# IPNET Agents WhatsApp

Repositorio-base para subir um agente de WhatsApp da IPNET com o framework `whatsapp-agent-framework`, usando Python local para desenvolvimento e Google Cloud Run para producao.

Este repo nao e o framework em si. Ele e o projeto do agente:

- prompt
- tools
- `.env`
- Dockerfile
- fluxo operacional de bootstrap
- documentacao para time interno

## O que este repo resolve

- padrao unico para um agente de WhatsApp
- caminho rapido para desenvolvimento local
- deploy no Cloud Run com Cloud SQL e Redis
- onboarding de colegas sem depender de contexto oral

## Arquitetura

```text
Usuario no WhatsApp
        |
        v
Evolution API
        |
        v
Cloud Run (main.py)
        |
        +--> Gemini
        +--> Cloud SQL PostgreSQL
        +--> Redis / Memorystore
```

## Estrutura do repo

```text
.
|-- .env.example
|-- Dockerfile
|-- Makefile
|-- README.md
|-- main.py
|-- prompts/
|   `-- system_prompt.md
|-- docs/
|   |-- cloudsql-postgres.md
|   |-- gcp-setup.md
|   |-- go-live-checklist.md
|   `-- local-development.md
|-- requirements.txt
`-- tools.py
```

## O que voce realmente edita

- `.env`: credenciais e configuracao
- `prompts/system_prompt.md`: comportamento do agente
- `tools.py`: logica e integracoes

`main.py` deve mudar pouco. Ele so carrega o prompt, registra tools e inicia o agente.

## Fluxo por perfil

### Se voce e gestor e o tecnico ainda nao tem acesso

Use o fluxo interno de concessao de acesso:

`https://dev.n8n.ipnetsolucoes.com.br/webhook/acessos-gcp-whatsapp-agent`

Esse e o caminho recomendado para criar ou liberar a Service Account de acesso do tecnico. O passo a passo completo esta em [docs/gcp-setup.md](/Users/Usuario/ipnet-agents-whatsapp/docs/gcp-setup.md).

### Se voce e tecnico e ja tem acesso

1. clone o repo
2. copie `.env.example` para `.env`
3. faca o setup local
4. ajuste prompt e tools
5. valide localmente
6. faca o deploy

## Quickstart tecnico

### 1. Clonar e instalar

```bash
git clone https://github.com/queziademetrioleo/ipnet-agents-whatsapp.git
cd ipnet-agents-whatsapp
cp .env.example .env
make setup
make help
```

### 2. Preencher o `.env`

Campos minimos:

- `IPNET_AGENT_NAME`
- `IPNET_INSTANCE_NAME`
- `IPNET_GEMINI_API_KEY`
- `IPNET_EVOLUTION_API_URL`
- `IPNET_EVOLUTION_API_KEY`
- `IPNET_POSTGRES_URL`
- `IPNET_REDIS_URL`
- `IPNET_SERVICE_ACCOUNT` se for deployar com SA explicita

Observacao importante:

- este starter envia as variaveis do `.env` para o Cloud Run via `--set-env-vars`
- por padrao, este repo nao integra Secret Manager
- se o time quiser Secret Manager, isso precisa ser implementado explicitamente no fluxo de deploy

### 3. Rodar localmente

```bash
make run
make health
```

Para QR code e status do WhatsApp:

```bash
make qrcode
make status
```

Guia completo de ambiente local:

- [docs/local-development.md](/Users/Usuario/ipnet-agents-whatsapp/docs/local-development.md)

## GCP e infraestrutura

O bootstrap de GCP foi separado em docs operacionais:

- [docs/gcp-setup.md](/Users/Usuario/ipnet-agents-whatsapp/docs/gcp-setup.md)
- [docs/cloudsql-postgres.md](/Users/Usuario/ipnet-agents-whatsapp/docs/cloudsql-postgres.md)
- [docs/go-live-checklist.md](/Users/Usuario/ipnet-agents-whatsapp/docs/go-live-checklist.md)

Essas docs cobrem:

- acesso inicial do tecnico
- APIs do projeto
- Cloud SQL
- PostgreSQL
- Redis / Memorystore
- VPC Connector
- Runtime Service Account
- Cloud Build Service Account
- deploy
- validacao pos-deploy

## Deploy

### Deploy base

```bash
make deploy \
  PROJECT_ID=SEU_PROJECT_ID \
  REGION=us-central1 \
  SERVICE=ipnet-whatsapp-agent \
  SQL_INSTANCE=SEU_PROJECT_ID:us-central1:whatsapp-agent-db
```

### Passo adicional obrigatorio para Redis

O comando `make deploy` faz o deploy base do servico e injeta variaveis do `.env`, mas ele nao configura automaticamente o VPC Connector do Cloud Run.

Depois do primeiro deploy, voce ainda precisa rodar o update do servico para anexar o connector e permitir acesso ao Memorystore. O comando exato esta em [docs/gcp-setup.md](/Users/Usuario/ipnet-agents-whatsapp/docs/gcp-setup.md).

### Logs

```bash
make logs \
  PROJECT_ID=SEU_PROJECT_ID \
  REGION=us-central1 \
  SERVICE=ipnet-whatsapp-agent
```

## Cloud SQL e PostgreSQL

Hoje o repo depende de PostgreSQL para:

- historico das conversas
- estado interno do agente via Agno

Pontos importantes:

- no Cloud Run, o host continua `127.0.0.1` por causa do Cloud SQL Auth Proxy
- localmente, voce pode usar PostgreSQL em Docker
- as tabelas do framework sao criadas automaticamente na primeira inicializacao bem-sucedida

Detalhes completos:

- [docs/cloudsql-postgres.md](/Users/Usuario/ipnet-agents-whatsapp/docs/cloudsql-postgres.md)

## Validacao minima antes do go-live

1. `make run` sobe sem erro
2. `make health` responde `ok`
3. QR code e status do WhatsApp funcionam
4. Cloud SQL esta `RUNNABLE`
5. Redis esta `READY`
6. Cloud Run responde no endpoint de health
7. Webhook da Evolution API aponta para a URL correta

Checklist completo:

- [docs/go-live-checklist.md](/Users/Usuario/ipnet-agents-whatsapp/docs/go-live-checklist.md)

## Comandos uteis

```bash
make help
make setup
make run
make health
make qrcode
make status
make deploy PROJECT_ID=... REGION=... SERVICE=... SQL_INSTANCE=...
make logs PROJECT_ID=... REGION=... SERVICE=...
```

## Dependencias e compatibilidade

- este repo depende do framework `whatsapp-agent-framework`
- o `requirements.txt` fixa `agno<2` porque o framework atual ainda usa a API 1.x do Agno

## Limites atuais do starter

- nao ha integracao nativa com Secret Manager neste repo
- o VPC Connector ainda e configurado manualmente no pos-deploy
- o starter traz tools placeholder; voce precisa trocar por integracoes reais antes de producao

Esses limites nao impedem uso interno, mas precisam estar claros para o time.

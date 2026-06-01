# IPNET WhatsApp Agent

Projeto-base para criar, configurar e publicar um agente de WhatsApp da IPNET com o framework `whatsapp-agent-framework`.

Este repositório existe para resolver um problema operacional: permitir que qualquer integrante do time consiga sair do zero e colocar um agente no ar sem depender de contexto oral, tentativa e erro ou adivinhação de infraestrutura.

## O que este repositório contém

- aplicação do agente (`main.py`)
- prompt de sistema (`prompts/system_prompt.md`)
- tools e integrações (`tools.py`)
- configuração por ambiente (`.env.example`)
- automação local (`Makefile`, `compose.yaml`, `scripts/doctor.py`)
- documentação operacional para acesso, infraestrutura, banco, execução local, deploy e go-live (`docs/`)

## O que este repositório não é

Este repositório não é o framework compartilhado. O framework continua no pacote `whatsapp-agent-framework`. Este repositório é o projeto do agente que o time clona para operar.

## Arquitetura

```text
Cliente no WhatsApp
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

## Quem deve ler o quê

### Gestor

Se o técnico ainda não tem acesso ao projeto GCP, comece por:

- [docs/gcp-setup.md](docs/gcp-setup.md)

O fluxo oficial de concessão de acesso está neste endpoint interno:

`https://dev.n8n.ipnetsolucoes.com.br/webhook/acessos-gcp-whatsapp-agent`

### Técnico

Se você já tem acesso ao projeto GCP, siga esta ordem:

1. [Setup local](#setup-local)
2. [Configurar o agente](#configurar-o-agente)
3. [Executar localmente](#executar-localmente)
4. [Preparar GCP](#preparar-gcp)
5. [Fazer deploy](#fazer-deploy)
6. [Validar go-live](#validar-go-live)

## Estrutura do projeto

```text
.
|-- .env.example
|-- .gitignore
|-- Dockerfile
|-- Makefile
|-- README.md
|-- compose.yaml
|-- docs/
|   |-- README.md
|   |-- cloudsql-postgres.md
|   |-- gcp-setup.md
|   |-- go-live-checklist.md
|   |-- local-development.md
|   `-- troubleshooting.md
|-- main.py
|-- prompts/
|   `-- system_prompt.md
|-- requirements.txt
|-- scripts/
|   `-- doctor.py
`-- tools.py
```

## Setup local

### Pré-requisitos

- Python 3.11+
- Docker
- acesso à Gemini API
- acesso à Evolution API

### Passo 1: clonar o repositório

```bash
git clone https://github.com/queziademetrioleo/ipnet-agents-whatsapp.git
cd ipnet-agents-whatsapp
```

### Passo 2: criar o `.env`

```bash
cp .env.example .env
```

### Passo 3: subir PostgreSQL e Redis locais

```bash
make infra-up
```

Isso sobe:

- PostgreSQL em `127.0.0.1:5432`
- Redis em `127.0.0.1:6379`

### Passo 4: instalar dependências Python

```bash
make setup
```

### Passo 5: validar o ambiente

```bash
make doctor
make help
```

Se `make doctor` acusar placeholder ou variável ausente, corrija o `.env` antes de continuar.

## Configurar o agente

Você só deve mexer nestes pontos:

- `.env`
- `prompts/system_prompt.md`
- `tools.py`

### `.env`

Campos mínimos para desenvolvimento local:

```env
IPNET_AGENT_NAME=IPNET WhatsApp Agent
IPNET_INSTANCE_NAME=ipnet-whatsapp-agent
IPNET_GEMINI_API_KEY=AIza...
IPNET_EVOLUTION_API_URL=https://evolution.seudominio.com
IPNET_EVOLUTION_API_KEY=sua-chave
IPNET_POSTGRES_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agentdb
IPNET_REDIS_URL=redis://127.0.0.1:6379/0
```

### `prompts/system_prompt.md`

Use este arquivo para definir:

- papel do agente
- escopo
- regras de comportamento
- forma de resposta
- quando transferir para humano

### `tools.py`

Use este arquivo para:

- FAQ interna
- integrações com CRM
- registro de leads
- consulta de status
- operações seguras que o agente pode chamar

## Executar localmente

### Subir o agente

```bash
make run
```

### Validar healthcheck

```bash
make health
```

### Obter QR code

```bash
make qrcode
```

### Verificar status da conexão

```bash
make status
```

## Preparar GCP

O passo a passo completo está aqui:

- [docs/gcp-setup.md](docs/gcp-setup.md)
- [docs/cloudsql-postgres.md](docs/cloudsql-postgres.md)

Esse material cobre:

- acesso inicial do técnico
- APIs necessárias
- runtime Service Account
- Cloud Build Service Account
- Cloud SQL
- PostgreSQL
- Redis / Memorystore
- VPC Connector
- deploy
- validação final

### Observação importante sobre segredos

Hoje este repositório faz deploy usando `--set-env-vars`. Isso significa:

- o `.env` é a fonte de verdade para o deploy
- este projeto não usa Secret Manager nativamente
- se o time quiser migrar para Secret Manager, será preciso alterar o fluxo de deploy

## Fazer deploy

### Passo 1: preencher o `.env` de produção

Para Cloud Run:

- `IPNET_POSTGRES_URL` deve usar `127.0.0.1`
- `IPNET_REDIS_URL` deve usar o IP privado do Memorystore
- `IPNET_SERVICE_ACCOUNT` deve apontar para a runtime SA correta

### Passo 2: fazer o deploy base

```bash
make deploy \
  PROJECT_ID=SEU_PROJECT_ID \
  REGION=us-central1 \
  SERVICE=ipnet-whatsapp-agent \
  SQL_INSTANCE=SEU_PROJECT_ID:us-central1:whatsapp-agent-db
```

Esse passo faz:

- build da imagem
- push da imagem
- deploy do Cloud Run
- anexo do Cloud SQL
- envio das variáveis `IPNET_*` do `.env`

### Passo 3: anexar o VPC Connector para o Redis

O deploy base não configura automaticamente o acesso privado ao Redis.

Você ainda precisa rodar o comando de update descrito em:

- [docs/gcp-setup.md](docs/gcp-setup.md)

Sem isso, o agente sobe, mas não consegue acessar o Memorystore.

### Passo 4: acompanhar logs

```bash
make logs \
  PROJECT_ID=SEU_PROJECT_ID \
  REGION=us-central1 \
  SERVICE=ipnet-whatsapp-agent
```

## Cloud SQL e PostgreSQL

Este agente depende de PostgreSQL para:

- histórico das conversas
- sessões internas do Agno

Pontos importantes:

- localmente, você pode usar o PostgreSQL do `compose.yaml`
- em Cloud Run, a conexão continua em `127.0.0.1` por causa do Cloud SQL Auth Proxy
- as tabelas são criadas automaticamente na primeira inicialização bem-sucedida

Detalhes completos:

- [docs/cloudsql-postgres.md](docs/cloudsql-postgres.md)

## Validar go-live

Checklist mínimo:

1. `make run` sobe sem erro
2. `make health` retorna `ok`
3. QR code e status funcionam
4. Cloud SQL está `RUNNABLE`
5. Redis está `READY`
6. Cloud Run responde
7. webhook da Evolution API aponta para a URL correta
8. teste ponta a ponta no WhatsApp funciona

Checklist completo:

- [docs/go-live-checklist.md](docs/go-live-checklist.md)

## Comandos disponíveis

| Comando | Finalidade |
|---|---|
| `make help` | Mostra os alvos disponíveis |
| `make infra-up` | Sobe PostgreSQL e Redis locais com Docker Compose |
| `make infra-down` | Derruba PostgreSQL e Redis locais |
| `make setup` | Cria `.venv` e instala dependências |
| `make doctor` | Valida `.env` e ferramentas locais |
| `make run` | Sobe o agente localmente |
| `make health` | Testa o endpoint `/webhook/health` |
| `make qrcode` | Busca QR code da instância na Evolution API |
| `make status` | Consulta o status da instância |
| `make deploy ...` | Faz build + push + deploy base no Cloud Run |
| `make logs ...` | Acompanha logs do Cloud Run |

## Documentação detalhada

- [docs/README.md](docs/README.md)
- [docs/local-development.md](docs/local-development.md)
- [docs/gcp-setup.md](docs/gcp-setup.md)
- [docs/cloudsql-postgres.md](docs/cloudsql-postgres.md)
- [docs/go-live-checklist.md](docs/go-live-checklist.md)
- [docs/troubleshooting.md](docs/troubleshooting.md)

## Dependências e compatibilidade

- este projeto depende do framework `whatsapp-agent-framework`
- `requirements.txt` fixa `agno<2` porque o framework atual ainda usa a API 1.x do Agno

## Limitações atuais

- não há integração nativa com Secret Manager neste projeto
- o VPC Connector ainda é um passo manual após o deploy base
- `tools.py` ainda é placeholder e precisa ser substituído pelas integrações reais do time

Essas limitações não impedem uso interno, mas precisam ser entendidas antes de produção.

# IPNET WhatsApp Agent

Projeto-base para criar, configurar e publicar um agente de WhatsApp da IPNET em um repositório único.

Este repositório existe para resolver um problema operacional: permitir que qualquer integrante do time consiga sair do zero e colocar um agente no ar sem depender de contexto oral, tentativa e erro ou adivinhação de infraestrutura.

## Objetivo

Com este repositório, uma pessoa nova no projeto deve conseguir:

1. obter acesso ao GCP correto
2. subir PostgreSQL e Redis localmente
3. preencher o `.env` sem ambiguidades
4. executar o agente localmente
5. validar QR code, webhook e healthcheck
6. fazer deploy no Cloud Run
7. validar a infraestrutura em produção

Se algum desses passos ainda exigir adivinhação, a documentação está incompleta.

## Sumario

- [Quem deve ler o que](#quem-deve-ler-o-que)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Setup local](#setup-local)
- [Configurar o agente](#configurar-o-agente)
- [Executar localmente](#executar-localmente)
- [Preparar GCP](#preparar-gcp)
- [Base de conhecimento](#base-de-conhecimento)
- [Fazer deploy](#fazer-deploy)
- [Validar go-live](#validar-go-live)
- [Comandos disponiveis](#comandos-disponiveis)
- [Documentacao detalhada](#documentacao-detalhada)

## O que este repositório contém

- aplicação do agente (`main.py`)
- prompt de sistema (`prompts/system_prompt.md`)
- tools e integrações (`app/tools.py`)
- base de conhecimento vetorial (`app/knowledge/`)
- persistência de leads (`app/repositories/`, `app/services/`)
- configuração por ambiente (`.env.example`)
- automação local (`Makefile`, `compose.yaml`, `scripts/doctor.py`, `scripts/ingest_knowledge.py`)
- documentação operacional para acesso, infraestrutura, banco, execução local, deploy e go-live (`docs/`)

## O que este repositório é

Este repositório já contém:

- runtime do agente
- webhook da Evolution API
- memória Redis
- histórico PostgreSQL
- CLI local de operação
- tools, prompt e base de conhecimento

Ou seja: o time não precisa depender de um segundo repositório para rodar este agente.

`whatsapp_agent_ipnet/` é esse motor local do agente. Ele ficou dentro deste repo porque agora o projeto é autossuficiente.

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

O objetivo desse fluxo e garantir que o tecnico receba o acesso certo antes de tocar na infraestrutura.

### Técnico

Se você já tem acesso ao projeto GCP, siga esta ordem:

1. [Setup local](#setup-local)
2. [Configurar o agente](#configurar-o-agente)
3. [Executar localmente](#executar-localmente)
4. [Preparar GCP](#preparar-gcp)
5. [Fazer deploy](#fazer-deploy)
6. [Validar go-live](#validar-go-live)

## Caminho mais curto para o primeiro sucesso

Se voce quer somente o caminho minimo para ver o agente funcionando localmente:

```bash
git clone https://github.com/queziademetrioleo/ipnet-agents-whatsapp.git
cd ipnet-agents-whatsapp
cp .env.example .env
make infra-up
make setup
make doctor
make run
```

Depois, em outro terminal:

```bash
make health
make qrcode
make status
```

Se `make doctor` apontar placeholder ou variavel ausente, corrija antes de prosseguir.

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
|   |-- rag.md
|   `-- troubleshooting.md
|-- app/
|   |-- config.py
|   |-- tools.py
|   |-- knowledge/
|   |-- repositories/
|   `-- services/
|-- main.py
|-- prompts/
|   `-- system_prompt.md
|-- requirements.txt
|-- scripts/
|   |-- doctor.py
|   `-- ingest_knowledge.py
`-- whatsapp_agent_ipnet/
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
make validate
make help
```

Se `make doctor` acusar placeholder ou variável ausente, corrija o `.env` antes de continuar.

## Configurar o agente

Você só deve mexer nestes pontos:

- `.env`
- `prompts/system_prompt.md`
- `app/tools.py`

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
IPNET_KNOWLEDGE_ENABLED=true
IPNET_EMBEDDING_MODEL=gemini-embedding-001
IPNET_EMBEDDING_DIMENSIONS=768
```

Referencia completa de variaveis:

- [docs/env-reference.md](docs/env-reference.md)

### `prompts/system_prompt.md`

Use este arquivo para definir:

- papel do agente
- escopo
- regras de comportamento
- forma de resposta
- quando transferir para humano

### `app/tools.py`

Use este arquivo para:

- FAQ interna
- integrações com CRM
- registro de leads
- consulta de status
- operações seguras que o agente pode chamar

## Base de conhecimento

O repo agora tem uma camada propria para RAG em `app/knowledge/`, separada das tools.

Fluxo:

1. arquivos fonte sao ingeridos por `scripts/ingest_knowledge.py`
2. o texto e quebrado em chunks
3. embeddings Gemini sao gerados
4. embeddings e chunks vao para o Postgres no schema `knowledge`
5. a tool `consultar_base_conhecimento` consulta essa base em runtime

Comando de ingestao:

```bash
make ingest-knowledge FILES="docs/faq.md docs/politicas.md"
```

Detalhes:

- [docs/rag.md](docs/rag.md)
- [docs/template-drone-agent.md](docs/template-drone-agent.md)

## Template pronto: agente de drone

Este repo ja foi preparado como exemplo funcional de um agente que tira duvidas sobre uso de drone.

Arquivos principais do template:

- [prompts/system_prompt.md](prompts/system_prompt.md)
- [app/tools.py](app/tools.py)
- [knowledge_seed/drone/faq-operacao.md](knowledge_seed/drone/faq-operacao.md)
- [knowledge_seed/drone/checklist-seguranca.md](knowledge_seed/drone/checklist-seguranca.md)
- [knowledge_seed/drone/cuidados-bateria.md](knowledge_seed/drone/cuidados-bateria.md)

Para carregar a base inicial:

```bash
make ingest-knowledge FILES="knowledge_seed/drone/faq-operacao.md knowledge_seed/drone/checklist-seguranca.md knowledge_seed/drone/cuidados-bateria.md"
```

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

Se o tecnico ainda nao tem acesso ao projeto, nao tente contornar isso com chave manual ou improviso. Use o fluxo do gestor documentado em [docs/gcp-setup.md](docs/gcp-setup.md).

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

Antes de rodar esse passo, confirme:

- `PROJECT_ID` esta correto
- `SERVICE` esta correto
- `SQL_INSTANCE` esta correto
- `IPNET_SERVICE_ACCOUNT` aponta para a runtime SA certa
- `IPNET_REDIS_URL` aponta para o IP privado do Memorystore, nao para localhost

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

Se qualquer um desses passos falhar, va direto para:

- [docs/troubleshooting.md](docs/troubleshooting.md)

Checklist completo:

- [docs/go-live-checklist.md](docs/go-live-checklist.md)

## Comandos disponiveis

| Comando | Finalidade |
|---|---|
| `make help` | Mostra os alvos disponíveis |
| `make infra-up` | Sobe PostgreSQL e Redis locais com Docker Compose |
| `make infra-down` | Derruba PostgreSQL e Redis locais |
| `make setup` | Cria `.venv` e instala dependências |
| `make doctor` | Valida `.env` e ferramentas locais |
| `make validate` | Faz validacao basica de sintaxe Python |
| `make run` | Sobe o agente localmente |
| `make health` | Testa o endpoint `/webhook/health` |
| `make qrcode` | Busca QR code da instância na Evolution API |
| `make status` | Consulta o status da instância |
| `make deploy ...` | Faz build + push + deploy base no Cloud Run |
| `make logs ...` | Acompanha logs do Cloud Run |

## Documentação detalhada

- [docs/README.md](docs/README.md)
- [docs/env-reference.md](docs/env-reference.md)
- [docs/local-development.md](docs/local-development.md)
- [docs/gcp-setup.md](docs/gcp-setup.md)
- [docs/cloudsql-postgres.md](docs/cloudsql-postgres.md)
- [docs/go-live-checklist.md](docs/go-live-checklist.md)
- [docs/troubleshooting.md](docs/troubleshooting.md)

## Dependências e compatibilidade

- o runtime do agente está versionado dentro deste repositório em `whatsapp_agent_ipnet/`
- `requirements.txt` fixa `agno<2` porque o runtime atual ainda usa a API 1.x do Agno

## Limitações atuais

- não há integração nativa com Secret Manager neste projeto
- o VPC Connector ainda é um passo manual após o deploy base
- `app/tools.py` ainda é o ponto principal para integrar sistemas reais do time

Essas limitações não impedem uso interno, mas precisam ser entendidas antes de produção.

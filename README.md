# IPNET Agents WhatsApp

Starter repo para subir um agente de WhatsApp da IPNET com o menor caminho possivel: clonar, configurar no VS Code, validar localmente e fazer deploy no Google Cloud Run.

## O que voce edita neste repo

Os pontos de customizacao ficaram concentrados em tres arquivos:

- `.env`: credenciais, URLs e configuracao de runtime
- `prompts/system_prompt.md`: comportamento do agente
- `tools.py`: funcoes que o agente pode chamar

O restante deve mudar pouco ou nada no dia a dia.

## Estrutura

```text
.
├── .env.example
├── Dockerfile
├── Makefile
├── README.md
├── main.py
├── prompts/
│   └── system_prompt.md
├── requirements.txt
└── tools.py
```

## Quickstart

### 1. Clonar e preparar o ambiente

```bash
git clone https://github.com/queziademetrioleo/ipnet-agents-whatsapp.git
cd ipnet-agents-whatsapp
cp .env.example .env
make setup
```

### 2. Preencher o `.env`

Voce vai precisar no minimo de:

- `IPNET_GEMINI_API_KEY`
- `IPNET_EVOLUTION_API_URL`
- `IPNET_EVOLUTION_API_KEY`
- `IPNET_INSTANCE_NAME`
- `IPNET_POSTGRES_URL`
- `IPNET_REDIS_URL`

Se a Service Account do Cloud Run ja existir, preencha tambem:

```env
IPNET_SERVICE_ACCOUNT=sua-sa@SEU_PROJECT_ID.iam.gserviceaccount.com
```

## Desenvolvimento local

O `main.py` e o starter estao corretos, mas o agente nao roda "sozinho" sem banco e Redis.

Para desenvolvimento local, use uma destas abordagens:

- mais simples: PostgreSQL e Redis locais
- mais proxima de producao: Cloud SQL + proxy local e um Redis acessivel pela sua maquina

Se quiser subir tudo local rapidamente, um caminho simples e:

```bash
docker run --name ipnet-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=agentdb -p 5432:5432 -d postgres:15
docker run --name ipnet-redis -p 6379:6379 -d redis:7
```

E no `.env`:

```env
IPNET_POSTGRES_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agentdb
IPNET_REDIS_URL=redis://127.0.0.1:6379/0
```

### 3. Ajustar o comportamento do agente

Edite:

- `prompts/system_prompt.md`
- `tools.py`

Regra pratica:

- mudou tom/comportamento -> edite o prompt
- mudou integracao/logica -> edite as tools

### 4. Rodar localmente

```bash
make run
```

O servidor sobe na porta `8080`.

Healthcheck local:

```bash
curl http://127.0.0.1:8080/webhook/health
```

## WhatsApp

Com a Evolution API configurada no `.env`, voce pode consultar QR code e status:

```bash
make qrcode
make status
```

## Deploy no GCP

### Pre-requisitos minimos

- `gcloud` autenticado
- projeto GCP selecionado
- Cloud SQL ja criado
- Redis ja criado
- service account ja criada ou permissao para criar uma
- Cloud Build com permissao para usar a service account do runtime

Se a SA ainda nao existir:

```bash
make setup-sa
```

Se a SA ja existir, basta deixar `IPNET_SERVICE_ACCOUNT` preenchido no `.env`.

### Bootstrap completo de GCP

O passo a passo completo de:

- APIs
- IAM
- Service Account
- Cloud Build
- Cloud SQL
- Redis
- VPC Connector
- validacoes finais

esta em [docs/gcp-setup.md](/Users/Usuario/ipnet-agents-whatsapp/docs/gcp-setup.md).

Se o tecnico ainda nao tiver uma Service Account de acesso criada pelo gestor, use tambem:

- [docs/service-account-setup.html](/Users/Usuario/ipnet-agents-whatsapp/docs/service-account-setup.html)

Esse HTML foi pensado para o gestor preencher os dados, criar a SA de provisionamento e liberar impersonation para o tecnico sem distribuir chave JSON.

### Deploy

```bash
make deploy \
  PROJECT_ID=SEU_PROJECT_ID \
  REGION=us-central1 \
  SERVICE=ipnet-whatsapp-agent \
  SQL_INSTANCE=SEU_PROJECT_ID:us-central1:whatsapp-agent-db
```

Depois do deploy, o comando retorna a URL publica do servico. Configure essa URL na Evolution API neste formato:

```text
https://SEU-SERVICO.run.app/webhook/IPNET_INSTANCE_NAME
```

## Fluxo recomendado de 48h

### Dia 1

1. Clonar o repo e preencher `.env`
2. Ajustar `system_prompt.md`
3. Ajustar `tools.py`
4. Rodar localmente
5. Validar QR code e recebimento de mensagens

### Dia 2

1. Validar infraestrutura no GCP
2. Fazer deploy no Cloud Run
3. Configurar webhook na Evolution API
4. Rodar teste ponta a ponta
5. Ajustar prompt e tools conforme os primeiros testes

## Notas importantes

- Este repo depende do framework `whatsapp-agent-framework`, fixado em `requirements.txt`.
- O `requirements.txt` fixa `agno<2` para manter compatibilidade com a API usada hoje pelo framework.
- Se voce atualizar a versao do framework, faca isso de forma intencional e teste o fluxo inteiro.
- O repo foi estruturado para um agente unico. Se voces passarem a operar varios agentes diferentes, vale separar framework e templates.

## Problemas comuns

### `whatsapp-agent: command not found`

O ambiente virtual nao foi criado ou ativado corretamente.

Rode:

```bash
make setup
```

### Erro no deploy usando service account

Confirme se:

- `IPNET_SERVICE_ACCOUNT` esta preenchido com o email da SA
- a Cloud Build SA tem permissao `roles/iam.serviceAccountUser` sobre essa SA

### QR code nao aparece

Confirme se:

- a Evolution API esta acessivel na URL do `.env`
- a API key esta correta
- a instancia existe ou pode ser criada pela integracao

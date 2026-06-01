# GCP Setup

Este documento cobre o bootstrap minimo de infraestrutura para este repo.

## 1. Pre-requisitos

- projeto GCP criado
- `gcloud` instalado
- conta autenticada no projeto correto

```bash
gcloud auth login
gcloud config set project SEU_PROJECT_ID
```

## 2. APIs necessarias

```bash
gcloud services enable \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  servicenetworking.googleapis.com \
  compute.googleapis.com
```

## 3. Permissoes minimas

### Se o tecnico ainda nao tiver acesso

Antes de qualquer bootstrap, o gestor pode criar uma SA de acesso/provisionamento para o tecnico usando:

- [service-account-setup.html](/Users/Usuario/ipnet-agents-whatsapp/docs/service-account-setup.html)

Fluxo esperado:

1. o gestor cria a SA de acesso
2. o gestor concede as roles do projeto para essa SA
3. o gestor libera `roles/iam.serviceAccountTokenCreator` e `roles/iam.serviceAccountUser` para o tecnico na SA
4. o tecnico usa `gcloud config set auth/impersonate_service_account ...`

Esse fluxo evita distribuir chave JSON e separa melhor o acesso humano do runtime do Cloud Run.

### Sua conta de desenvolvedor

Voce precisa de permissoes para:

- criar Cloud SQL
- criar Redis
- criar VPC Connector
- fazer deploy no Cloud Run
- atribuir IAM nas service accounts

Na pratica, as roles mais comuns sao:

- `roles/cloudsql.admin`
- `roles/redis.admin`
- `roles/compute.networkAdmin`
- `roles/run.admin`
- `roles/iam.serviceAccountAdmin`
- `roles/resourcemanager.projectIamAdmin`
- `roles/iam.serviceAccountUser`
- `roles/cloudbuild.builds.editor`

### Runtime Service Account do agente

Se a SA do agente ja existir, anote o email e coloque em `.env`:

```env
IPNET_SERVICE_ACCOUNT=sua-sa@SEU_PROJECT_ID.iam.gserviceaccount.com
```

Ela precisa, no minimo, destas roles no projeto:

- `roles/cloudsql.client`
- `roles/redis.editor`
- `roles/logging.logWriter`

### Cloud Build Service Account

O Cloud Build tambem precisa de permissoes para fazer o deploy:

```bash
PROJECT_NUMBER=$(gcloud projects describe SEU_PROJECT_ID --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
RUNTIME_SA="sua-sa@SEU_PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding SEU_PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding SEU_PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/storage.admin"

gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member="serviceAccount:$CB_SA" \
  --role="roles/iam.serviceAccountUser"
```

Sem isso, o build pode falhar no deploy com erro de `actAs` ou de permissao no Cloud Run.

## 4. Cloud SQL

```bash
gcloud sql instances create whatsapp-agent-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase

gcloud sql databases create agentdb \
  --instance=whatsapp-agent-db

gcloud sql users create agentuser \
  --instance=whatsapp-agent-db \
  --password=TROQUE_POR_UMA_SENHA_FORTE

gcloud sql instances describe whatsapp-agent-db \
  --format='value(connectionName)'
```

Guarde o `connectionName` retornado. Ele entra no deploy como `SQL_INSTANCE`.

## 5. Redis (Memorystore)

```bash
gcloud redis instances create whatsapp-agent-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic

gcloud redis instances describe whatsapp-agent-redis \
  --region=us-central1 \
  --format='value(host)'
```

Guarde o IP retornado. Ele entra no `.env` como `IPNET_REDIS_URL`.

## 6. VPC Connector

Para o Cloud Run falar com o Memorystore, crie o connector:

```bash
gcloud compute networks vpc-access connectors create whatsapp-agent-connector \
  --region=us-central1 \
  --network=default \
  --range=10.8.0.0/28
```

Verificacao:

```bash
gcloud compute networks vpc-access connectors describe whatsapp-agent-connector \
  --region=us-central1 \
  --format='value(state)'
```

## 7. Preenchimento do `.env`

Exemplo dos campos principais:

```env
IPNET_SERVICE_ACCOUNT=sua-sa@SEU_PROJECT_ID.iam.gserviceaccount.com
IPNET_POSTGRES_URL=postgresql+asyncpg://agentuser:SENHA@127.0.0.1:5432/agentdb
IPNET_REDIS_URL=redis://10.x.x.x:6379/0
```

## 8. Deploy deste repo

No repo:

```bash
make deploy \
  PROJECT_ID=SEU_PROJECT_ID \
  REGION=us-central1 \
  SERVICE=ipnet-whatsapp-agent \
  SQL_INSTANCE=SEU_PROJECT_ID:us-central1:whatsapp-agent-db
```

Depois do primeiro deploy, conecte o Redis ao servico:

```bash
gcloud run services update ipnet-whatsapp-agent \
  --region=us-central1 \
  --vpc-connector=whatsapp-agent-connector \
  --vpc-egress=private-ranges-only \
  --update-env-vars="IPNET_REDIS_URL=redis://10.x.x.x:6379/0" \
  --service-account=sua-sa@SEU_PROJECT_ID.iam.gserviceaccount.com
```

## 9. Validacoes finais

```bash
gcloud run services describe ipnet-whatsapp-agent \
  --region=us-central1 \
  --format='value(status.url)'

gcloud sql instances describe whatsapp-agent-db \
  --format='value(state)'

gcloud redis instances describe whatsapp-agent-redis \
  --region=us-central1 \
  --format='value(state)'
```

Estado esperado:

- Cloud Run com URL publica
- Cloud SQL em `RUNNABLE`
- Redis em `READY`

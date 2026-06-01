# Cloud SQL e PostgreSQL

Este repo usa PostgreSQL para persistencia de conversa e estado interno do agente.

## O que fica no PostgreSQL

- historico das mensagens por numero
- sessoes internas do Agno

Tabelas esperadas:

- `ipnet_conversation_history`
- `ipnet_agno_sessions`

## Criar a instancia no GCP

```bash
gcloud sql instances create whatsapp-agent-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=HDD \
  --storage-size=10GB \
  --no-storage-auto-increase \
  --no-backup
```

## Criar banco e usuario

```bash
gcloud sql databases create agentdb \
  --instance=whatsapp-agent-db

gcloud sql users create agentuser \
  --instance=whatsapp-agent-db \
  --password=TROQUE_POR_UMA_SENHA_FORTE
```

## Obter o connection name

```bash
gcloud sql instances describe whatsapp-agent-db \
  --format='value(connectionName)'
```

Formato esperado:

```text
SEU_PROJECT_ID:us-central1:whatsapp-agent-db
```

Esse valor entra no deploy como `SQL_INSTANCE`.

## Strings de conexao

### Desenvolvimento local com Docker

```env
IPNET_POSTGRES_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/agentdb
```

### Cloud Run com Cloud SQL Auth Proxy

```env
IPNET_POSTGRES_URL=postgresql+asyncpg://agentuser:SENHA@127.0.0.1:5432/agentdb
```

Importante:

- no Cloud Run, continua sendo `127.0.0.1`
- o acesso real ao Cloud SQL vem de `--add-cloudsql-instances` no deploy
- a runtime SA precisa de `roles/cloudsql.client`

## Como validar a conexao

Verifique o estado da instancia:

```bash
gcloud sql instances describe whatsapp-agent-db \
  --format='value(state)'
```

Resultado esperado:

```text
RUNNABLE
```

## Conectar no banco para inspecionar

```bash
gcloud sql connect whatsapp-agent-db \
  --user=agentuser \
  --database=agentdb
```

No `psql`:

```sql
\dt

SELECT phone, role, content, created_at
FROM ipnet_conversation_history
ORDER BY created_at DESC
LIMIT 20;
```

## Erros comuns

### `Cloud SQL client does not have permission to access the instance`

Causa comum:

- runtime SA sem `roles/cloudsql.client`

### O servico sobe mas nao conecta no banco

Checklist:

- `SQL_INSTANCE` correto no deploy
- `IPNET_POSTGRES_URL` com usuario, senha e nome do banco corretos
- Cloud SQL em `RUNNABLE`
- SA do Cloud Run com `roles/cloudsql.client`

### Tabelas nao aparecem

As tabelas so aparecem quando o agente sobe com conexao valida ao PostgreSQL.

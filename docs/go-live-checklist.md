# Go-live checklist

Checklist minimo antes de colocar o agente em producao.

## 1. Acesso

- tecnico com acesso ao projeto GCP
- Service Account de runtime definida
- Cloud Build SA com permissao de deploy

## 2. Infraestrutura

- APIs do projeto habilitadas
- Cloud SQL criado
- banco `agentdb` criado
- usuario `agentuser` criado
- Redis criado
- VPC Connector criado

## 3. Configuracao do repo

- `.env` preenchido
- `IPNET_POSTGRES_URL` validado
- `IPNET_REDIS_URL` validado
- `IPNET_SERVICE_ACCOUNT` validado
- prompt revisado
- tools revisadas

## 4. Validacao local

- `make setup`
- `make run`
- `make health`
- `make qrcode`
- `make status`

## 5. Deploy

- `make deploy PROJECT_ID=... REGION=... SERVICE=... SQL_INSTANCE=...`
- `gcloud run services update ... --vpc-connector=...`

## 6. Pos-deploy

- URL publica do Cloud Run respondendo
- healthcheck funcionando
- webhook configurado na Evolution API
- Cloud SQL em `RUNNABLE`
- Redis em `READY`
- logs chegando no Cloud Logging

## 7. Teste ponta a ponta

- enviar mensagem real pelo WhatsApp
- confirmar recebimento no webhook
- confirmar resposta do agente
- confirmar persistencia no Postgres
- confirmar uso do Redis sem timeout

# Troubleshooting

## `make run` falha logo ao iniciar

Verifique:

- `.env` existe
- `IPNET_POSTGRES_URL` esta correto
- `IPNET_REDIS_URL` esta correto
- Gemini API key esta valida

Use:

```bash
make doctor
```

## `make health` falha

Se o servico nao estiver rodando, o healthcheck vai falhar.

Suba primeiro:

```bash
make run
```

## Erro ao conectar no PostgreSQL

Checklist:

- Postgres esta rodando
- porta 5432 esta livre
- usuario/senha/banco batem com o `.env`

Com Docker Compose:

```bash
make infra-up
```

## Erro ao conectar no Redis

Checklist:

- Redis esta rodando
- porta 6379 esta acessivel
- `IPNET_REDIS_URL` esta correto

## Deploy falha no Cloud Run

Checklist:

- `gcloud auth login` feito
- projeto correto no `PROJECT_ID`
- runtime SA correta em `IPNET_SERVICE_ACCOUNT`
- Cloud Build SA com `roles/iam.serviceAccountUser` sobre a runtime SA

## Deploy sobe, mas o agente nao acessa Redis

O deploy base nao configura automaticamente o VPC Connector.

Rode o `gcloud run services update ... --vpc-connector=...` descrito em [gcp-setup.md](gcp-setup.md).

## QR code nao aparece

Checklist:

- Evolution API acessivel
- API key correta
- instancia correta em `IPNET_INSTANCE_NAME`
- instancia nao esta ja conectada

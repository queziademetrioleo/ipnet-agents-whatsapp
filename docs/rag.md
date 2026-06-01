# Base de Conhecimento e RAG

O starter agora possui uma camada propria de base de conhecimento em `app/knowledge/`.

## O que existe hoje

- `chunking.py`: quebra documentos em trechos menores
- `embeddings.py`: gera embeddings com Gemini
- `vector_store.py`: persiste documentos e embeddings no PostgreSQL usando `pgvector`
- `retriever.py`: busca vetorial por similaridade
- `service.py`: orquestra ingestao e consulta
- `scripts/ingest_knowledge.py`: comando de carga inicial

## Estrutura no banco

Schema padrao: `knowledge`

Tabelas:

- `knowledge.documents`
- `knowledge.chunks`

O schema e criado automaticamente no primeiro uso. O codigo tambem tenta criar a extensao `vector`.

## Ingestao

Com o `.env` preenchido:

```bash
make ingest-knowledge FILES="docs/faq.md docs/politicas.md"
```

Cada arquivo e lido, quebrado em chunks e salvo no Postgres junto com o embedding.

## Consulta em runtime

O agente recebe duas tools relevantes:

- `consultar_base_conhecimento`
- `consultar_faq`

`consultar_faq` tenta usar a base vetorial primeiro. Se a base estiver indisponivel, cai no FAQ fallback em memoria.

## Cuidados

- o Postgres precisa aceitar `CREATE EXTENSION vector`
- `IPNET_GEMINI_API_KEY` precisa estar configurada para gerar embeddings
- a base vetorial usa o mesmo Postgres do agente, mas em schema separado

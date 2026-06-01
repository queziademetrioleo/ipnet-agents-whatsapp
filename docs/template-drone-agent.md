# Template de Agente: Tira-Duvidas de Drone

Este repositorio ja pode ser usado como template de um agente de suporte para usuarios de drone.

## O que foi preparado

- prompt de sistema focado em operacao segura de drone
- tools de checklist pre-voo e manutencao basica
- tool de consulta de base de conhecimento
- tool para registrar caso de suporte humano
- base inicial em CSV em `knowledge_seed/drone/`

## Como usar como template

1. ajuste [prompts/system_prompt.md](../prompts/system_prompt.md) para a marca, linha ou publico do drone
2. ajuste [app/tools.py](../app/tools.py) se quiser incluir orientacoes por modelo
3. ingira a base inicial:

```bash
make ingest-knowledge FILES="knowledge_seed/drone/rag_dji_mini_3_pro_100_qa.csv"
```

4. teste localmente com perguntas como:
   - "meu drone nao decola"
   - "como saber se a bateria esta ruim?"
   - "o que eu verifico antes do primeiro voo?"
   - "a imagem esta tremendo, o que pode ser?"

## Extensoes recomendadas

- adicionar documento por modelo de drone
- adicionar limites e mensagens de seguranca especificos do fabricante
- adicionar procedimentos de calibracao por modelo
- adicionar perguntas frequentes sobre app e controle remoto

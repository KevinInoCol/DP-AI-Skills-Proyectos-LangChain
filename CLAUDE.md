# Agente Municipal — LangChain v1

Agente de atención ciudadana (RAG de trámites + Tavily + fecha/hora) con memoria
en Postgres, expuesto por FastAPI.

@.claude/rules/langchain-mcp-first.md

## Convenciones (skills en `.claude/skills/`)

- Estructura de carpetas y dónde va cada cosa → `agent-project-structure`
- Formato del prompt (`prompt/system_prompt.yaml`) → `agent-prompt-yaml-format`
- API vigente de LangChain 1.x → `langchain-mcp-docs` (guías) + `langchain-mcp-reference` (firmas)
- Cabecera de cada `.py` → `python-module-structure`
- Modelo por defecto `gpt-4.1` → `default-llm-model`
- Nombre de la colección del vector store → `rag-tenant-collection-naming`
- Los valores del `.env` no se leen ni se imprimen → `env-secrets-use-dont-read`

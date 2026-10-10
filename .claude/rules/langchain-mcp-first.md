# Regla: LangChain MCP primero

Antes de escribir o modificar código que importe `langchain`, `langchain_core`,
`langgraph`, `langchain_postgres`, `langchain_openai` o `langchain_tavily`,
consulta la MCP `docs-langchain` (y `reference-langchain` para firmas exactas).
La API 1.x rompió con 0.x y el conocimiento previo del modelo mezcla ambas.
Ver skills `langchain-mcp-docs` y `langchain-mcp-reference`.

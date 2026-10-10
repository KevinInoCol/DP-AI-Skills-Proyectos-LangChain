# Migraciones SQL

Pegar en el SQL Editor de Supabase **en este orden**. Todas son idempotentes.

| # | Archivo | Cuándo |
|---|---|---|
| 1 | `001_extension_vector.sql` | Antes de la primera ingesta (`python -m RAG.rag`) |
| 2 | `002_conversation_log.sql` | Antes de levantar la API |
| 3 | `003_rls.sql` | **Después** del primer arranque de la API y de la primera ingesta: las tablas del checkpointer y de PGVector las crean `PostgresSaver.setup()` y `langchain-postgres` |

El agente se conecta con el rol dueño de las tablas, que ignora RLS. Activarlo
sin políticas solo cierra el acceso por PostgREST (anon key) a las conversaciones.

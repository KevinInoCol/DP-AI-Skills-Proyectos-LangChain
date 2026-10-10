---
name: default-llm-model
description: Specifies the user's default LLM model preference (GPT-4.1) for all projects. Use when configuring, instantiating, or selecting an LLM/chat model — including LlamaIndex `OpenAI(...)`, LangChain `ChatOpenAI(...)`, raw `openai` SDK calls, Vercel AI SDK provider config, prompt YAML/JSON config files, environment variables (e.g., `OPENAI_MODEL`), or any new project scaffold. Apply this preference automatically without asking.
---

# Default LLM Model Preference

The user's standing preference: **always default to GPT-4.1 from OpenAI** for any new or existing project, unless the user explicitly asks for a different model in the current request.

## Model IDs to use

| Use case | Model ID (string) |
|---|---|
| **Default** (general reasoning, RAG, agents, chat) | `gpt-4.1` |
| Cost-sensitive / high-volume / simple tasks | `gpt-4.1-mini` |
| Ultra-cheap classification / cleanup | `gpt-4.1-nano` |
| Embeddings (unchanged — OpenAI default) | `text-embedding-3-small` or `text-embedding-3-large` |

Unless context strongly suggests otherwise, use plain `gpt-4.1`.

## Where to apply it

Whenever you write or modify any of the following, the model field must be `gpt-4.1`:

1. **LlamaIndex** — `from llama_index.llms.openai import OpenAI; OpenAI(model="gpt-4.1", ...)`
2. **LangChain** — `from langchain_openai import ChatOpenAI; ChatOpenAI(model="gpt-4.1", ...)`
3. **OpenAI SDK direct** — `client.chat.completions.create(model="gpt-4.1", ...)` or `client.responses.create(model="gpt-4.1", ...)`
4. **Vercel AI SDK** — `openai("gpt-4.1")`
5. **YAML/JSON prompt configs** — `model.name: gpt-4.1`, `model: gpt-4.1`
6. **Env vars** — `OPENAI_MODEL=gpt-4.1`, `LLM_MODEL=gpt-4.1`
7. **`.env.example` and README snippets** — same value
8. **Existing legacy models** to silently upgrade unless the user asked to preserve them:
   - `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`, `gpt-4` → upgrade to `gpt-4.1`

## How to apply it

- **Do not ask** which model to use. Default to `gpt-4.1` silently.
- If the user explicitly names a different model in the same request ("usa gpt-4o", "use claude-sonnet-4-6"), honor that — the explicit instruction overrides this default for that request only.
- When upgrading an existing project, mention briefly in your reply ("usé `gpt-4.1` por tu preferencia global") so the user knows it was applied — don't bury the change.
- If the project pins a specific model in a config file with a clear reason (a comment, a CHANGELOG entry, an eval lock), surface the conflict to the user rather than overwriting.

## When NOT to apply it

- Non-OpenAI LLMs (Anthropic, Google, Mistral, local) — use the user's per-provider preference or ask.
- Embedding models — use `text-embedding-3-small` by default; don't put `gpt-4.1` in an embedding slot.
- Image, audio or other modality-specific endpoints — use the modality-appropriate model.
- When the user is studying an older model behavior on purpose (course exercise comparing models, for instance) — ask first.

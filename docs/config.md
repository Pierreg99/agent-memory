# Configuration reference

Settings are Pydantic models loaded from YAML. The packaged file
[`agent_memory/config/defaults.yaml`](../agent_memory/config/defaults.yaml)
is always the base.

## Resolution order

1. Packaged `defaults.yaml`
2. File at `MEMORY_CONFIG_PATH` (if set) — deep-merged
3. `AgentMemory.from_config(overrides)` / `load_settings(overrides)` — deep-merged last

`AgentMemory.from_yaml(path)` replaces the packaged defaults entirely with
that file’s contents (it does not merge `MEMORY_CONFIG_PATH`).

Invalid enum values raise `ValueError` with the allowed options listed.
A missing `MEMORY_CONFIG_PATH` target raises `FileNotFoundError`.

## window

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `strategy` | `sliding` \| `truncate_oldest` \| `summarize_old` | `sliding` | Summarize-old still uses sliding for the kept window; the orchestrator writes summaries. |
| `max_tokens` | int | `4000` | Hard ceiling including reserved response tokens. |
| `keep_last_turns` | int | `12` | Soft floor for sliding; ignored by truncate-oldest. |
| `reserve_for_response` | int | `800` | Subtracted from `max_tokens` to form the prompt budget. |
| `pin_system_prompt` | bool | `true` | Reserved for callers that pin a system prompt; system tokens are counted when `prepare(..., system_prompt=...)` is used. |

## tokens

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `backend` | `heuristic` \| `tiktoken` | `heuristic` | Tiktoken requires the optional extra. |
| `tiktoken_encoding` | str | `cl100k_base` | Used when backend is tiktoken. |
| `chars_per_token` | float | `4.0` | Heuristic density; non-empty text counts as at least 1 token. |

Per-message overhead is 3 tokens (role framing approximation).

## summary

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `backend` | `extractive` \| `llm` | `extractive` | LLM path uses `ResilientSummarizer` (falls back to extractive). |
| `trigger_when_tokens_over` | int | `3000` | Orchestrator trigger under summarize-old. |
| `max_summary_tokens` | int | `400` | Passed into the summarizer. |
| `min_messages_to_summarize` | int | `4` | Extractive returns empty below this count. |
| `llm.model` | str | `gpt-4o-mini` | Chat-completions model id. |
| `llm.api_key_env` | str | `OPENAI_API_KEY` | Env var name holding the key (never hard-code secrets). |
| `llm.endpoint` | str | OpenAI chat completions URL | Any compatible endpoint. |
| `llm.temperature` | float | `0.2` | Sampling temperature. |

## vector

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | bool | `true` | Disable to skip RAG entirely. |
| `backend` | `hash` \| `sentence_transformers` | `hash` | Hash is deterministic and dependency-free. |
| `dim` | int | `128` | Overridden by the real model dim for sentence-transformers. |
| `top_k` | int | `4` | Default retrieve count in `prepare`. |
| `min_similarity` | float | `0.0` | Cosine similarity floor. |
| `model_name` | str | `all-MiniLM-L6-v2` | Sentence-transformers model id. |

## persistence

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | bool | `true` | False installs a no-op store. |
| `sqlite_path` | str | `:memory:` | Use a file path for durability / shared threads. |
| `auto_commit` | bool | `true` | Commit after each mutating operation. |
| `save_long_term_on_add` | bool | `true` | Reserved flag for future selective persistence. |

## session

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `default_id` | str | `default` | Used when `session_id` is omitted. |
| `clear_on_start` | bool | `false` | Reserved for application-level startup hooks. |

## Example override file

```yaml
window:
  strategy: summarize_old
  max_tokens: 8000
  reserve_for_response: 1000
summary:
  backend: extractive
  trigger_when_tokens_over: 5000
vector:
  top_k: 6
persistence:
  sqlite_path: ./data/agent_mem.db
```

```bash
export MEMORY_CONFIG_PATH=./my_memory.yaml
```

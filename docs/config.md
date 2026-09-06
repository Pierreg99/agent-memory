# Configuration reference

Settings are Pydantic models loaded from YAML. The packaged
[`agent_memory/config/defaults.yaml`](../agent_memory/config/defaults.yaml)
is always the base.

## Resolution order

1. Packaged `defaults.yaml`
2. File at `MEMORY_CONFIG_PATH` (if set) — deep-merged
3. `AgentMemory.from_config(overrides)` / `load_settings(overrides)` — deep-merged last

`AgentMemory.from_yaml(path)` uses that file directly.

## window

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `strategy` | enum | `sliding` | `sliding`, `truncate_oldest`, or `summarize_old`. |
| `max_tokens` | int | `4000` | Total prompt-side hard ceiling before reserved response tokens. |
| `keep_last_turns` | int | `12` | Soft preference; never overrides the hard ceiling. |
| `reserve_for_response` | int | `800` | Reserved for the model response. |
| `pin_system_prompt` | bool | `true` | System text is retained when possible; pathological oversized prompts are trimmed to preserve the hard ceiling. |

## tokens

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `backend` | enum | `heuristic` | `heuristic` or `tiktoken`. |
| `tiktoken_encoding` | str | `cl100k_base` | Encoding when tiktoken is selected. |
| `chars_per_token` | float | `4.0` | Positive heuristic density. |

Per-message overhead is approximated at 3 tokens.

## summary

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `backend` | enum | `extractive` | `extractive` or `llm`; LLM failures fall back to extraction. |
| `trigger_when_tokens_over` | int | `3000` | Trigger for `summarize_old`. |
| `max_summary_tokens` | int | `400` | Summary output budget. |
| `min_messages_to_summarize` | int | `4` | Minimum message count for a summary batch. |
| `llm.model` | str | `gpt-4o-mini` | Chat-completions model identifier. |
| `llm.api_key_env` | str | `OPENAI_API_KEY` | Environment variable name for the secret. |
| `llm.endpoint` | str | OpenAI URL | OpenAI-compatible chat-completions endpoint. |
| `llm.temperature` | float | `0.2` | Sampling temperature. |

## vector

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | bool | `true` | Enables semantic recall. |
| `backend` | enum | `hash` | `hash` or `sentence_transformers`. |
| `dim` | int | `128` | Positive dimension; real model dimension is adopted automatically. |
| `top_k` | int | `4` | Maximum retrieved entries before final prompt fitting. |
| `min_similarity` | float | `0.0` | Cosine-similarity threshold between -1 and 1. |
| `model_name` | str | `all-MiniLM-L6-v2` | Sentence-transformers model id. |
| `persist_embeddings` | bool | `true` | Persist vectors in SQLite and rebuild the index on restart. |

## persistence

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | bool | `true` | False uses a no-op store. |
| `sqlite_path` | str | `:memory:` | File path for durability; `:memory:` is process-local. |
| `auto_commit` | bool | `true` | Commit after mutating operations. |
| `save_long_term_on_add` | bool | `true` | Compatibility flag retained for existing configs. |

## retention

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | bool | `false` | Enables retention enforcement. |
| `days` | int | `0` | Positive number of days to retain; zero disables purge. |
| `run_on_start` | bool | `false` | Purge expired persisted data during initialization. |

Example:

```yaml
retention:
  enabled: true
  days: 30
  run_on_start: true
```

## session

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `default_id` | str | `default` | Used when no explicit session ID is supplied. |
| `clear_on_start` | bool | `false` | Clears the default session at initialization. |

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
  persist_embeddings: true
persistence:
  sqlite_path: ./data/agent_mem.db
retention:
  enabled: true
  days: 30
```

```bash
export MEMORY_CONFIG_PATH=./my_memory.yaml
```

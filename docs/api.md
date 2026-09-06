# API reference

Public exports live on the top-level `agent_memory` package. Prefer
`AgentMemory` for application code; lower-level types are available for
custom wiring and tests.

## AgentMemory

### Constructors

| Method | Description |
|--------|-------------|
| `AgentMemory(settings, counter=None, window=None, summarizer=None, store=None, vector=None)` | Explicit wiring; omitted pieces are built from `settings`. Persistent vectors are restored automatically when enabled. |
| `AgentMemory.from_config(overrides=None)` | Load packaged defaults (+ optional `MEMORY_CONFIG_PATH`), then deep-merge `overrides`. |
| `AgentMemory.from_yaml(path)` | Load a YAML file. Raises `FileNotFoundError` / `ValueError` on bad input. |

### Ingest

| Method | Description |
|--------|-------------|
| `add(role, content, session_id=None, metadata=None)` | Persist one message; rejects empty content. |
| `add_user` / `add_assistant` / `add_system` | Role-specific helpers; extra kwargs become metadata. |
| `add_long_term(content, session_id=None, importance=1.0, metadata=None)` | Persist a long-term fact and embed it when vector memory is enabled. |
| `add_many_long_term(facts, …)` | Batch helper returning the created entries. |

### Context assembly

```python
pack = mem.prepare(query_text, session_id=None, system_prompt=None)
```

`prepare()` loads the session, optionally advances summary coverage, retrieves
semantic memories, and performs a final token-budget fit over the fully rendered
system context plus recent messages. `MemoryPack.used_tokens` reports the final
fitted prompt-side estimate and never exceeds `budget_tokens`.

### Lifecycle and privacy

| Method | Description |
|--------|-------------|
| `default_session` | `settings.session.default_id`. |
| `clear_session(session_id=None)` | Deletes messages, summaries, long-term facts, and persisted vectors for the session. |
| `export_session(session_id=None)` | Returns JSON-serializable session data, including persisted embeddings. |
| `purge_expired(now=None)` | Applies the configured timestamp-based retention policy. |
| `stats(session_id=None)` | Counts memory records and current vector index size. |
| `close()` | Closes the current thread's SQLite connection. |

## MemoryPack

| Field | Meaning |
|-------|---------|
| `session_id` | Active session |
| `system_prompt` | Budget-fitted system prompt |
| `recent_messages` | Recent turns that fit the final budget |
| `summary` | Latest summary text, if any |
| `summary_covers` | Message IDs covered by the latest summary |
| `retrieved_facts` | Highest-ranked session-scoped memory hits that fit |
| `used_tokens` / `budget_tokens` | Final prompt-side token estimate / configured prompt budget |

`to_chat_messages()` builds a single synthesized system message when needed,
followed by recent messages in chronological order.

## Core models

- **Message** — `id`, `role`, `content`, `timestamp`, `metadata`, optional cached `token_count`.
- **MemoryEntry** — `kind`, `session_id`, `content`, optional `embedding`, `source_message_ids`, bounded `importance`, and `metadata`.
- **MemoryQuery** — session-scoped query with bounded `top_k` and `min_importance`.

## Subsystems

| Class | Role |
|-------|------|
| `HeuristicTokenCounter` / `TiktokenTokenCounter` | Text/message token estimation |
| `WindowManager` | Strict prompt-side windowing |
| `ExtractiveSummarizer` / `LLMSummarizer` / `ResilientSummarizer` | Text and message summarization |
| `HashEmbedder` / `SentenceTransformersEmbedder` | Embedding backends |
| `VectorMemory` | Thread-safe in-process vector index with restore/upsert support |
| `MemoryStore` | SQLite persistence for messages, summaries, facts, and persisted vectors |

Factories: `build_counter`, `build_summarizer`, and `build_embedder` are
available from their respective modules.

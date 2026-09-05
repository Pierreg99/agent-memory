# API reference

Public exports live on the top-level `agent_memory` package. Prefer
`AgentMemory` for application code; lower-level types are available for
custom wiring and tests.

```python
from agent_memory import (
    AgentMemory,
    MemorySettings,
    load_settings,
    Message,
    MemoryEntry,
    MemoryQuery,
    MemoryPack,
    Role,
    MemoryKind,
    WindowStrategy,
    SummarizerBackend,
    EmbeddingBackend,
    WindowManager,
    HeuristicTokenCounter,
    TokenCounter,
    Summarizer,
    ExtractiveSummarizer,
    ResilientSummarizer,
    VectorMemory,
    MemoryStore,
)
```

Version: `agent_memory.__version__`.

## AgentMemory

### Constructors

| Method | Description |
|--------|-------------|
| `AgentMemory(settings, counter=None, window=None, summarizer=None, store=None, vector=None)` | Explicit wiring; omitted pieces are built from `settings`. |
| `AgentMemory.from_config(overrides=None)` | Load packaged defaults (+ optional `MEMORY_CONFIG_PATH`), deep-merge `overrides`. |
| `AgentMemory.from_yaml(path)` | Load a YAML file. Raises `FileNotFoundError` / `ValueError` on bad input. |

When `persistence.enabled` is false, a no-op store is used (ingest does
not accumulate). When `vector.enabled` is false, `prepare()` returns no
retrieved facts.

### Ingest

| Method | Description |
|--------|-------------|
| `add(role, content, session_id=None, metadata=None)` | Persist one message. Rejects empty content and unknown roles (`ValueError`). |
| `add_user` / `add_assistant` / `add_system` | Role-specific helpers; extra kwargs become metadata. |
| `add_long_term(content, session_id=None, importance=1.0, metadata=None)` | Persist a long-term fact and embed it when vector memory is enabled. |
| `add_many_long_term(facts, …)` | Batch helper returning the created entries. |

### Context assembly

```python
pack = mem.prepare(
    query_text,
    session_id=None,       # defaults to settings.session.default_id
    system_prompt=None,    # when set, stored system messages are dropped from recent
)
```

Returns a `MemoryPack` with recent messages, optional summary text,
retrieved facts, and token accounting.

### Session helpers

| Method / property | Description |
|-------------------|-------------|
| `default_session` | `settings.session.default_id` |
| `clear_session(session_id=None)` | Clears store rows and vector entries for that session only. |
| `stats(session_id=None)` | `message_count`, `long_term_count`, `vector_count` (store-wide length), `total_tokens`, `budget_tokens`. |

## MemoryPack

| Field | Meaning |
|-------|---------|
| `session_id` | Active session |
| `system_prompt` | Optional prompt passed into `prepare` |
| `recent_messages` | Windowed conversation turns |
| `summary` | Latest summary text, if any |
| `summary_covers` | Message ids covered by that summary |
| `retrieved_facts` | Top-k `MemoryEntry` hits |
| `used_tokens` / `budget_tokens` | Window accounting |

`to_chat_messages()` builds an OpenAI-style list:

1. One synthesized `system` message (prompt + summary + facts), if any
   of those are present.
2. Then each recent message as `{role, content}`.

## Core models

- **Message** — `id`, `role`, `content`, `timestamp`, `metadata`, optional
  cached `token_count`.
- **MemoryEntry** — `kind`, `session_id`, `content`, optional `embedding`,
  `source_message_ids`, `importance`, `metadata`.
- **MemoryQuery** — `session_id`, `query_text`, `top_k`, `kinds`,
  `min_importance`, `metadata_filter`.

## Subsystems (for custom wiring)

| Class | Role |
|-------|------|
| `HeuristicTokenCounter` / `TiktokenTokenCounter` | `count_text` / `count_messages` |
| `WindowManager` | `apply(messages, system_prompt=None) -> WindowResult` |
| `ExtractiveSummarizer` / `LLMSummarizer` / `ResilientSummarizer` | Text and message summarization |
| `HashEmbedder` / `SentenceTransformersEmbedder` | Embedding backends |
| `VectorMemory` | `add`, `query`, `clear`, `clear_session` |
| `MemoryStore` | SQLite messages / summaries / long-term tables; `file_store(path)` helper |

Factories: `build_counter`, `build_summarizer`, `build_embedder`
(available from their modules).

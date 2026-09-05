# Architecture

Agent Memory is a small, composable memory layer for LLM agents. Every
serious agent eventually needs four capabilities; this library provides
them as replaceable subsystems behind one orchestrator.

| Concern | Subsystem | Module |
|---------|-----------|--------|
| How long is the prompt? | Token counter | `window/token_counter.py` |
| Which turns fit? | Window manager | `window/window_manager.py` |
| What about dropped turns? | Summarizer | `summary/summarizer.py` |
| What does the agent know? | Vector memory (RAG) | `vector/memory.py` |
| Where does it live? | Persistence | `persistence/store.py` |
| Who glues it together? | Orchestrator | `agent_memory.py` |

## Data flow

```
                           ┌────────────────────────┐
                           │       AgentMemory      │  ← single public entry
                           └────────────┬───────────┘
                                        │
            ┌───────────────┬───────────┼───────────┬───────────────┐
            ▼               ▼           ▼           ▼               ▼
     WindowManager    Summarizer   VectorMemory   MemoryStore   TokenCounter
            │               │           │           │               │
        kept msgs      older turns   top-k facts   raw data      token counts
            │               │           │           │               │
            └───────────────┴─────┬─────┴───────────┘               │
                                  ▼                                 │
                          MemoryPack (Pydantic)  ◄─────────────────┘
                                  │
                                  ▼
                      pack.to_chat_messages()
                                  │
                                  ▼
                      OpenAI / Anthropic / local LLM
```

`prepare()` is an intentional pipeline — no hidden side effects beyond
optional summary persistence when `window.strategy == summarize_old`:

1. Load session messages from the store.
2. If summarize-old is active and the token trigger is exceeded, compress
   the oldest chunk (leaving the most recent quarter untouched) and
   persist a `MemoryEntry(kind=SUMMARY)` with `source_message_ids`.
3. Apply the window manager to select recent messages that fit the budget
   (system prompt tokens are reserved when provided).
4. Retrieve top-k long-term / summary facts for `query_text`, scoped to
   the session.
5. Bundle everything as a `MemoryPack`.

## Design choices

1. **One orchestrator, four pluggable subsystems.** Token counters,
   summarizers, and embedders implement small Protocols so you can swap
   implementations without changing call sites.

2. **Pydantic at the boundary.** Messages, entries, queries, packs, and
   settings are typed models. Invalid config fails early with clear
   messages instead of producing malformed prompts.

3. **YAML as the source of truth.** Packaged `defaults.yaml` is always
   the base. Optional `MEMORY_CONFIG_PATH` and `from_config(overrides)`
   deep-merge on top.

4. **Zero required external services.** Defaults use
   `HeuristicTokenCounter`, `HashEmbedder`, `ExtractiveSummarizer`, and
   in-process SQLite. Optional adapters cover `tiktoken`,
   `sentence-transformers`, and OpenAI-compatible chat completions.

5. **Auditable summarization.** Every summary stores
   `source_message_ids` so you can trace compressed text back to the
   turns it covered.

6. **Session-aware vector recall.** `VectorMemory.query` filters by
   `session_id`, kind, importance, metadata, and similarity.
   `clear_session` drops only that session’s vector entries.

7. **Thread-local SQLite connections.** Schema is applied on every new
   connection so worker threads are interchangeable. Prefer a file path
   (not `:memory:`) when multiple threads must share state — SQLite
   `:memory:` databases are per-connection.

## Configuration knobs

| Field | Purpose | Default |
|-------|---------|---------|
| `window.strategy` | `sliding` / `truncate_oldest` / `summarize_old` | `sliding` |
| `window.max_tokens` | Hard ceiling for the prompt | `4000` |
| `window.keep_last_turns` | Floor for recent turns (sliding) | `12` |
| `window.reserve_for_response` | Tokens reserved for the reply | `800` |
| `tokens.backend` | `heuristic` / `tiktoken` | `heuristic` |
| `summary.backend` | `extractive` / `llm` | `extractive` |
| `summary.trigger_when_tokens_over` | Compress when over this | `3000` |
| `summary.max_summary_tokens` | Summary budget | `400` |
| `vector.enabled` | Toggle RAG | `true` |
| `vector.backend` | `hash` / `sentence_transformers` | `hash` |
| `vector.top_k` | Facts to retrieve | `4` |
| `persistence.sqlite_path` | `:memory:` or file | `:memory:` |

See [config.md](config.md) for the complete field list.

## Extension points

- **Custom token counter** — implement `TokenCounter`, pass
  `AgentMemory(..., counter=...)`.
- **Custom summarizer** — implement `Summarizer`, pass
  `summarizer=...`.
- **Custom embedder** — implement `Embedder`, pass into
  `VectorMemory(..., embedder=...)`.
- **Custom store** — match the methods `AgentMemory` calls
  (`add_message`, `get_messages`, `add_summary`, `get_latest_summary`,
  `add_long_term`, `get_long_term`, `clear_session`) and pass
  `store=...`.

## When to use what

| Stack | Fit |
|-------|-----|
| Defaults | Prototyping, demos, agents that must run offline |
| + tiktoken | Exact token accounting for known model families |
| + sentence-transformers | Semantic retrieval beyond lexical hash overlap |
| + LLM summarizer | Long chats where extractive scoring loses nuance |
| File-backed SQLite | Cross-process persistence and shared threads |
| Custom store | Multi-tenant isolation or hosted databases |

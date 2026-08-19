# Agent Memory System — Architecture

A modular, configurable memory layer for LLM agents. Every LLM agent
eventually needs four things, and this library provides all four as
small, composable pieces:

| Concern | Subsystem | Module |
|---|---|---|
| How long is the prompt? | Token counter | `window/token_counter.py` |
| Which turns fit in the window? | Window manager | `window/window_manager.py` |
| What about the turns we dropped? | Summarizer | `summary/summarizer.py` |
| What does the agent know about the user? | Vector memory (RAG) | `vector/memory.py` |
| Where does all this live between sessions? | Persistence | `persistence/store.py` |
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

## Key design choices

1. **One orchestrator, four pluggable subsystems.** Each subsystem
   implements a `Protocol` so you can swap implementations freely
   (e.g. tiktoken → custom tokenizer, hash → sentence-transformers,
   extractive → LLM-based summarization).

2. **Pydantic everywhere.** All inputs/outputs are typed models, so
   configuration errors are caught at the boundary instead of producing
   malformed prompts downstream.

3. **YAML-driven configuration.** `config/defaults.yaml` is the source
   of truth. `load_settings(overrides=...)` deep-merges overrides, so
   application code only specifies what differs from the defaults.

4. **Zero required external services.** The default stack uses
   `HeuristicTokenCounter`, `HashEmbedder`, `ExtractiveSummarizer`,
   and an in-process SQLite store. Optional adapters exist for
   `tiktoken`, `sentence-transformers`, and any OpenAI-compatible
   chat-completions endpoint.

5. **Auditable summarization.** Every `MemoryEntry(kind=SUMMARY)`
   stores `source_message_ids`, so you can trace any summary back to
   the exact turns it was derived from.

6. **Thread-safe persistence.** Each thread gets its own SQLite
   connection; the schema is applied on every new connection so
   per-thread connections are interchangeable.

7. **No magic in the orchestrator.** `AgentMemory.prepare()` is a
   straightforward pipeline: load → maybe-summarize → window → retrieve
   → bundle. Every step has a clear input and output.

## Configuration knobs

| Field | Purpose | Default |
|---|---|---|
| `window.strategy` | `sliding` / `truncate_oldest` / `summarize_old` | `sliding` |
| `window.max_tokens` | Hard ceiling for the prompt | `4000` |
| `window.keep_last_turns` | Always keep at least this many turns | `12` |
| `window.reserve_for_response` | Reserve tokens for the reply | `800` |
| `tokens.backend` | `heuristic` / `tiktoken` | `heuristic` |
| `summary.backend` | `extractive` / `llm` | `extractive` |
| `summary.trigger_when_tokens_over` | Compress when over this | `3000` |
| `summary.max_summary_tokens` | Compress summary to ≤ this | `400` |
| `vector.enabled` | Toggle RAG | `true` |
| `vector.backend` | `hash` / `sentence_transformers` | `hash` |
| `vector.top_k` | How many facts to retrieve | `4` |
| `persistence.sqlite_path` | `":memory:"` or a file | `":memory:"` |

## Extension points

- **Custom token counter** — implement `TokenCounter` and pass to
  `AgentMemory(..., counter=...)`.
- **Custom summarizer** — implement `Summarizer` and pass to
  `AgentMemory(..., summarizer=...)`.
- **Custom embedder** — implement `Embedder` and pass to
  `VectorMemory(..., embedder=...)`.
- **Custom store** — implement the same methods as `MemoryStore` and
  pass to `AgentMemory(..., store=...)`.

## When to use what

- **Default stack** — perfect for prototyping, small-to-medium agents,
  and any situation where you want zero infrastructure dependencies.
- **Add tiktoken** — when you need exact token accounting and your
  model has a well-known tokenizer.
- **Add sentence-transformers** — when lexical overlap is too noisy
  and you need real semantic retrieval.
- **Add an LLM summarizer** — when conversations are long and the
  extractive heuristic drops important nuance.
- **Swap the store** — when you need cross-process persistence,
  multi-tenant isolation, or a hosted database.

## Related documentation

- See [ROADMAP.md](../ROADMAP.md) for the active progress plan and planned future subsystems.
- See [CHANGELOG.md](../CHANGELOG.md) for release version history.

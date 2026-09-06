# Architecture

Agent Memory is a small, composable memory layer for LLM agents. It separates
prompt windowing, summarization, semantic recall, persistence, and token
accounting behind one orchestrator.

| Concern | Subsystem | Module |
|---------|-----------|--------|
| How long is the prompt? | Token counter | `window/token_counter.py` |
| Which turns fit? | Window manager | `window/window_manager.py` |
| What about dropped turns? | Summarizer | `summary/summarizer.py` |
| What does the agent know? | Vector memory | `vector/memory.py` |
| Where does it live? | Persistence | `persistence/store.py` |
| Who glues it together? | Orchestrator | `agent_memory.py` |

## Data flow

```text
                           ┌────────────────────────┐
                           │       AgentMemory      │
                           └────────────┬───────────┘
                                        │
            ┌───────────────┬───────────┼───────────┬───────────────┐
            ▼               ▼           ▼           ▼               ▼
     WindowManager    Summarizer   VectorMemory   MemoryStore   TokenCounter
            │               │           │           │               │
        kept msgs      older turns   top-k facts   durable data   token counts
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

## `prepare()` pipeline

1. Load all messages for the session.
2. Under `summarize_old`, identify message IDs not already covered by the latest summary and summarize an older subset when the configured trigger is exceeded.
3. Window recent messages using the prompt-side budget.
4. Retrieve session-scoped long-term facts and summaries from the vector index.
5. Perform a second, final fit over the fully rendered system context plus recent messages so retrieval and summaries cannot overflow the budget.
6. Return a `MemoryPack` ready for an LLM SDK.

## Persistence lifecycle

Long-term entries and generated summaries can be embedded and persisted in a
SQLite `memory_vectors` table. On startup the orchestrator restores those
entries into the in-process index. Incompatible embedding dimensions are
re-embedded from stored content so model changes do not permanently break the
index.

`clear_session()` removes every layer for one session. `export_session()` emits
JSON-serializable records. `purge_expired()` deletes old records across all
persistent layers according to the configured retention window.

## Design choices

1. **One orchestrator, pluggable subsystems.** Token counters, summarizers, and embedders implement small interfaces.
2. **Typed boundaries.** Pydantic models validate core memory values and query limits.
3. **Configuration-first behavior.** Packaged YAML is the base, with environment and runtime overrides.
4. **No required external service.** Defaults work offline with SQLite, hash embeddings, heuristic tokens, and extractive summaries.
5. **Auditable summarization.** Summary entries retain source message IDs.
6. **Session-scoped recall.** Queries default to the active session.
7. **Operational lifecycle.** Persistence, deletion, export, retention, and restart reconstruction are explicit APIs.

## Scaling notes

The built-in vector index remains O(N) and is appropriate for small deployments.
For larger corpora, keep the `VectorMemory` abstraction and replace it with a
persistent ANN/vector database such as FAISS, Qdrant, or pgvector. A hosted
application should additionally enforce tenant authorization, encryption at
rest, audit logging, and provider-specific data retention controls.

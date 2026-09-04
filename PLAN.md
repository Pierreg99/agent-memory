# Technical Execution Plan & Design Principles

This document outlines the design principles, subsystem architecture, and execution plan for the `agent-memory` library.

## Architectural Objectives

1. **Modular Subsystem Protocol**: Each core component (Token Counter, Window Manager, Summarizer, Vector Memory, Persistence Store) adheres to a clear interface or protocol, allowing developers to plug in custom backends.
2. **Zero Mandatory Heavy Dependencies**: Out of the box, `agent-memory` runs with lightweight dependencies (`pydantic`, `numpy`, `pyyaml`, `requests`). Optional heavy packages like `tiktoken` or `sentence-transformers` are lazy-loaded when configured.
3. **Pydantic Validation at Boundaries**: Data structures passed into or returned from memory operations (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`) are strictly validated Pydantic models.
4. **Declarative YAML Configuration**: All default settings live in `defaults.yaml` and can be overridden via dictionary options or custom YAML files.

---

## Subsystem Pipeline Execution

```
[Incoming User Query]
         │
         ▼
[AgentMemory.prepare()]
         │
         ├───► 1. Load Session Messages (SQLite Store)
         │
         ├───► 2. Check Summary Trigger (If tokens > threshold & strategy == summarize_old)
         │        └──► Summarize Oldest Chunk -> Persist Summary Entry
         │
         ├───► 3. Apply Context Windowing (WindowManager)
         │        └──► Fit messages into (max_tokens - reserve_for_response)
         │
         ├───► 4. Retrieve RAG Long-Term Facts (VectorMemory)
         │        └──► Cosine Similarity Query filtered by kind/importance/metadata
         │
         └───► 5. Pack Context (MemoryPack)
                  └──► Ready for chat LLM consumption via pack.to_chat_messages()
```

---

## Testing & Verification Strategy

- **Unit Testing**: Isolated tests for individual components (`test_token_counter.py`, `test_models.py`, `test_config.py`).
- **Subsystem Integration Testing**: Testing windowing strategies, summarization triggers, SQLite persistence, and vector similarity retrieval (`test_window.py`, `test_summary.py`, `test_persistence.py`, `test_vector.py`).
- **End-to-End Testing**: Full orchestrator testing (`test_orchestrator.py`) validating message ingestion, context packing, and session management.
- **Linting & Formatting**: Enforcement of strict typing and PEP 8 standards via `ruff check .`.

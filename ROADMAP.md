# Project Roadmap & Progress

This document outlines the development status, current progress, and future roadmap for `agent-memory`.

## Progress & Completed Milestones

- [x] **v0.1.0 Initial Core Release**
  - Modular orchestrator (`AgentMemory`) integrating context windowing, summarization, vector retrieval, and persistence.
  - Pydantic models (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`) for robust type safety.
  - Token-aware context windowing with sliding window, truncation, and old-turn summarization.
  - Pluggable vector memory with hash-based default embeddings and optional `sentence-transformers` integration.
  - Thread-safe SQLite persistence layer.
  - YAML configuration with deep-merge overrides.
  - 48 unit & integration test coverage.
  - GitHub Actions publishing workflow.

## Upcoming Roadmap

### Short-Term (v0.2.0)
- [ ] **Async Native API**: Add async support (`AsyncAgentMemory`) for high-throughput asyncio agent frameworks.
- [ ] **Expanded Vector Backends**: Support external vector databases (e.g., Qdrant, ChromaDB, PGVector) alongside internal SQLite vector store.
- [ ] **Enhanced Summarization Strategies**: Introduce hierarchical, graph-based, or multi-turn conversational chunk summarizers.

### Medium-Term (v0.3.0+)
- [ ] **Structured Memory Extraction**: Automatic background entity/fact extraction from conversation turns.
- [ ] **Episodic & Semantic Memory Separation**: Formalize memory layers into working context, episodic history, and semantic knowledge stores.
- [ ] **Telemetry & Observability**: OpenTelemetry instrumentation for monitoring context usage, token efficiency, and vector search latency.

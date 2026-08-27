# Agent Memory Roadmap

This document outlines the strategic vision and feature roadmap for `agent-memory`. The roadmap is organized into iterative milestones focused on performance, modularity, scale, and developer experience.

---

## Milestone 1: Async Support & Core Performance (v0.2.0)

- [ ] **Asynchronous API Extensions**:
  - Provide `AsyncAgentMemory` with `async add_user()`, `async prepare()`, and `async add_long_term()` methods.
  - Implement async SQLite persistence via `aiosqlite` for non-blocking database operations.
- [ ] **Batch Embedding Computation**:
  - Vectorize hash embedding and sentence-transformer batch processing for multi-message ingest.
- [ ] **Memory Inspection API**:
  - Add filtering and search utilities for session message logs and retrieved long-term memory entries.

---

## Milestone 2: External Vector Store Adapters (v0.3.0)

- [ ] **Pluggable Vector Databases**:
  - Add native adapters for ChromaDB, FAISS, Qdrant, and Pinecone.
  - Support hybrid keyword (BM25) and dense vector search capabilities.
- [ ] **Custom Metadata Expressions**:
  - Support rich comparison operators (e.g., `>`, `<`, `in`) in `MemoryQuery` metadata filters.

---

## Milestone 3: Advanced Summarization & Memory Lifecycle (v0.4.0)

- [ ] **Hierarchical Summarization Trees**:
  - Multi-level compression (turn-level -> session-level -> global user profile) for long-running agent threads.
- [ ] **Memory Decay & Forgetting**:
  - Implement time-weighted exponential decay for long-term fact relevance scores.
- [ ] **Conflict Resolution & Fact Merging**:
  - Automated detection and merging of updated user preferences (e.g., updating location or preferences).

---

## Milestone 4: Telemetry, Tooling & Production Readiness (v1.0.0)

- [ ] **OpenTelemetry & Observability**:
  - Add tracing spans for token counting, context windowing, RAG retrieval, and summarization latency.
- [ ] **Interactive Memory CLI**:
  - Developer CLI tool to inspect SQLite databases, run vector queries, and simulate memory context generation.
- [ ] **Multi-Tenant Isolation**:
  - Fine-grained tenant and session authorization wrappers for enterprise agent deployments.

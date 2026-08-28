# Agent Memory Roadmap

This document outlines the project development status, current features, planned enhancements, and long-term vision for **Agent Memory**.

---

## 📊 Current Status (v0.1.0)

Agent Memory provides a production-ready, lightweight, and modular memory layer for LLM agents with zero mandatory external services.

### Implemented Features
- [x] **Context Windowing**: Token-aware sliding, truncation, and automatic summarization strategies.
- [x] **Pluggable Token Counters**: Fast heuristic counter with optional `tiktoken` support.
- [x] **Flexible Summarizers**: Rule-based extractive summarization and OpenAI-compatible LLM summarizer with graceful fallback.
- [x] **Vector / Long-Term Recall**: In-memory vector store with deterministic hashing and optional `sentence-transformers` embeddings.
- [x] **Persistence**: Thread-safe SQLite store supporting file-backed and in-memory databases.
- [x] **Configurability**: YAML-driven defaults with runtime override support.
- [x] **Testing & CI**: Comprehensive test suite and automated PyPI publishing GitHub Actions workflow.

---

## 🎯 Short-Term Focus (v0.2.0)

### 1. Vector Database Integration
- [ ] Add async/sync adapters for persistent vector stores (e.g., Qdrant, ChromaDB, PGVector).
- [ ] Support hybrid search combining keyword/lexical search and dense vector embeddings.

### 2. Enhanced Memory Lifecycle
- [ ] Memory decay and importance scoring adjustments based on access frequency and time elapsed.
- [ ] Automatic fact extraction pipeline from incoming user messages.
- [ ] Memory deduplication and consolidation routines for long-running sessions.

### 3. Asynchronous API Support
- [ ] Provide async versions of core operations (`add_user_async`, `prepare_async`, etc.).
- [ ] Async SQLite / database engine integration for high-concurrency environments.

---

## 🚀 Mid-Term Vision (v0.3.0 - v0.5.0)

### 1. Multi-Agent & Structured Memory
- [ ] Shared memory spaces across multiple agent instances.
- [ ] Graph-based structured memory relationships (entity-attribute-value / knowledge graphs).
- [ ] Role-based access control and memory scoping per session, user, or organization.

### 2. Advanced Observability & Tooling
- [ ] Exportable telemetry and inspection tools for memory retrieval debuggers.
- [ ] Interactive visualization CLI/UI for viewing active agent memory contexts and vector recall.

---

## 🔮 Long-Term Vision

To become the standard, lightweight, and framework-agnostic memory engine for AI agents across Python and other runtime ecosystems, emphasizing privacy, speed, transparency, and minimal infrastructure overhead.

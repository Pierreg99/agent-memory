# Agent Memory — Product Roadmap

This roadmap outlines the planned development milestones, feature enhancements, and strategic direction for the `agent-memory` library.

---

## Milestone 1: Core Foundation (v0.1.0) — *Current Release*

- [x] High-level orchestrator (`AgentMemory`)
- [x] Sliding, truncate-oldest, and summarize-old context windowing
- [x] Extractive summarization & LLM summarization adapter
- [x] In-memory vector store with hash & sentence-transformers embeddings
- [x] Thread-safe SQLite persistence
- [x] YAML-based deep-merge configuration system
- [x] Pydantic typed data models and 48 unit/integration tests

---

## Milestone 2: Enhanced RAG & Storage Adapters (v0.2.0) — *Short Term*

- [ ] **Vector Database Adapters**:
  - Native integration adapters for ChromaDB, Qdrant, and Pinecone.
- [ ] **Advanced RAG Capabilities**:
  - Metadata filtering for vector recall (e.g. filter memories by tag, topic, or timestamp).
  - Hybrid search (combining BM25 lexical keyword search with dense vector similarity).
- [ ] **Memory Expiration & Decay**:
  - Recency weighting and time-decay functions for memory score ranking.
  - Automatic memory pruning for stale or low-importance entries.

---

## Milestone 3: Multimodal & Multi-Agent Memory (v0.3.0) — *Medium Term*

- [ ] **Multi-Agent / Multi-Session Sharing**:
  - Shared memory namespaces across multiple agents or sub-agents.
  - Granular access controls (private vs. shared agent memories).
- [ ] **Multimodal Memory Support**:
  - Support for image/audio/document context entries and multimodal embeddings.
- [ ] **Async & Distributed Support**:
  - Native `asyncio` APIs (`AsyncAgentMemory`) for high-concurrency event loops.
  - PostgreSQL / Redis storage backends for scalable distributed deployments.

---

## Milestone 4: Enterprise & Observability (v1.0.0) — *Long Term*

- [ ] **Observability & Tracing**:
  - OpenTelemetry integration for tracing memory retrieval latency and token consumption.
  - Visual memory inspector UI tool for debugging memory recall and summarization lineage.
- [ ] **Privacy & Compliance**:
  - Automatic PII (personally identifiable information) scrubbing before memory storage.
  - Right-to-be-forgotten / deletion API by user ID or entity tag.

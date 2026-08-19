# Agent Memory — Product Roadmap & Progress Plan

This document outlines the vision, completed milestones, active development progress, and future development plan for the `agent-memory` Python library.

---

## 🎯 Vision

`agent-memory` aims to be the lightweight, modular, and configurable standard memory layer for LLM agents. It provides token-aware context window management, automatic background summarization, long-term RAG recall, and thread-safe persistence — with zero required cloud dependencies out of the box.

---

## 📊 Progress Summary

| Milestone | Status | Key Features | Target / Release |
|---|---|---|---|
| **v0.1.0 (Initial Release)** | ✅ Completed | Core Orchestrator, Heuristic/Tiktoken counters, Sliding/Summarize-old strategies, Extractive/LLM summarizer, Hash/SentenceTransformers embedder, SQLite store, YAML settings | Jan 2025 |
| **v0.1.1 (Patch & Stability)** | 🔄 Current | Window manager floor fixes, metadata flexibility, comprehensive CHANGELOG & ROADMAP | Feb 2025 |
| **v0.2.0 (Vector & RAG Scale)** | 📅 Planned | SQLite Vector extension / FAISS adapter, metadata filtering query builder, hybrid lexical-dense search | Q2 2025 |
| **v0.3.0 (Advanced Memory Management)** | 📅 Planned | Working memory scratchpad, automatic importance decay, memory consolidation & deduplication | Q3 2025 |
| **v1.0.0 (Production Hardening)** | 📅 Planned | Multi-process connection pooling, Async API support, official framework integrations (LangChain, LlamaIndex, AutoGen) | Q4 2025 |

---

## 🗺️ Detailed Roadmap

### Phase 1: Core Foundation & Stability (v0.1.x) — Current Focus

- [x] **Modular Subsystem Protocol**: Define strict Protocols for TokenCounter, Summarizer, Embedder, and MemoryStore.
- [x] **YAML & Pydantic Configuration**: Full type-checked settings with deep-merge override support.
- [x] **Context Windowing**: Sliding window, truncate oldest, response budget reservation, system prompt pinning.
- [x] **Extractive & LLM Summarizer**: Fast offline keyword summarizer + resilient OpenAI-compatible LLM summarizer with graceful fallback.
- [x] **Deterministic Vector Store**: In-process HashEmbedder for zero-dependency RAG + optional sentence-transformers.
- [x] **SQLite Persistence**: Thread-safe per-thread connections with file or `:memory:` storage.
- [x] **Fix Window Floor Logic**: Enforce `keep_last_turns` floor even under tight token budgets.
- [x] **Flexible Metadata**: Support explicit `metadata` dict or arbitrary keyword args across `add_user`, `add_assistant`, `add_system`.

### Phase 2: Enhanced RAG & Retrieval Scaling (v0.2.0)

- [ ] **Vector Persistence & Indexing**: Persistent embeddings storage in SQLite or pluggable FAISS / Qdrant backend.
- [ ] **Hybrid Search**: Reciprocal Rank Fusion (RRF) combining keyword BM25 search with dense vector similarity.
- [ ] **Advanced Query Filtering**: Expression-based query filtering for temporal ranges, roles, and complex metadata tags.
- [ ] **Memory Decay & Recency Scoring**: Recency-weighted score boosting so recent memories score higher than old ones.

### Phase 3: Memory Lifecycle & Consolidation (v0.3.0)

- [ ] **Working Memory Scratchpad**: Ephemeral scratchpad for intermediate task state during multi-step reasoning.
- [ ] **Automated Memory Consolidation**: Periodic background jobs that combine similar long-term facts and remove duplicates.
- [ ] **Importance Scoring Heuristics**: Automatic importance rating for key entities, user preferences, and explicit instructions.
- [ ] **Fact Verification / Hallucination Guard**: Cross-reference generated summaries with source message IDs before persistence.

### Phase 4: Enterprise & Ecosystem Integration (v1.0.0)

- [ ] **Async Native API**: `AsyncAgentMemory` for high-throughput asyncio agent servers (FastAPI/Tornado).
- [ ] **Connection Pooling & Multi-Tenancy**: Distributed persistence drivers (PostgreSQL / Redis) for scale-out agent fleets.
- [ ] **Framework Adapters**: First-class adapters for LangChain, LlamaIndex, AutoGen, and CrewAI.
- [ ] **Observability & Inspection UI**: Built-in CLI and Web UI for inspecting context windows, token usage, and memory packs.

---

## 💬 Feedback & Contributions

Suggestions and contributions are welcome! Feel free to open issues or pull requests on [GitHub](https://github.com/Pierreg99/agent-memory).

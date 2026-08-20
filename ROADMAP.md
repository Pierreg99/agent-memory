# Agent Memory — Project Roadmap & Progress Plan

This document outlines the development roadmap, current progress, and planned milestones for the `agent-memory` library.

---

## 🎯 Vision

Provide a modular, dependency-light, and token-aware context and memory management engine for LLM agents. `agent-memory` aims to be the standard memory layer for AI agents across local prototyping, lightweight server deployments, and enterprise production environments.

---

## 📊 Current Status & Progress Summary

| Subsystem / Area | Status | Key Highlights |
|---|---|---|
| **Orchestrator** | ✅ Completed (v0.1.0) | `AgentMemory` class with YAML & dict config support, turn ingestion, and `MemoryPack` assembly. |
| **Context Windowing** | ✅ Completed (v0.1.0) | `WindowManager` supporting sliding, truncate-oldest, and summarize-old strategies. |
| **Token Counter** | ✅ Completed (v0.1.0) | Heuristic token counter (default) and optional `tiktoken` adapter. |
| **Summarization Engine** | ✅ Completed (v0.1.0) | Keyword-scoring `ExtractiveSummarizer`, OpenAI-compatible `LLMSummarizer`, and `ResilientSummarizer` fallback handler. |
| **Vector Memory (RAG)** | ✅ Completed (v0.1.0) | `HashEmbedder` (zero-dep) and optional `SentenceTransformersEmbedder` with cosine similarity retrieval. |
| **Durable Persistence** | ✅ Completed (v0.1.0) | Thread-safe SQLite store supporting memory or file databases, auto-commits, and indexed sessions. |
| **Test Suite** | ✅ Completed (v0.1.0) | Unit and integration tests covering all subsystems. |

---

## 🗺️ Roadmap Milestones

### Phase 1: Core Foundation & Stability (v0.1.x — Current)
- [x] Initial release of modular `agent-memory` library.
- [x] Zero-dependency default stack (`HeuristicTokenCounter`, `HashEmbedder`, `ExtractiveSummarizer`, SQLite).
- [x] Pydantic models for type safety across all messages, entries, and packs.
- [x] Runnable end-to-end multi-turn demo (`examples/run_demo.py`).
- [x] Comprehensive documentation and initial `CHANGELOG.md` / `ROADMAP.md`.

### Phase 2: Enhanced Integrations & Async Support (v0.2.0 — Short Term)
- [ ] **Async Support (`AsyncAgentMemory`)**:
  - Asynchronous store operations using `aiosqlite`.
  - Non-blocking LLM summarization calls and vector query execution.
- [ ] **Expanded LLM & Embedding Adapters**:
  - Native Anthropic (Claude) and Cohere summarizer adapters.
  - HuggingFace Inference API and Ollama embedding backends.
- [ ] **Enhanced Memory Pruning & Decay**:
  - Recency-weighted importance scoring for long-term facts.
  - Automatic eviction / consolidation policies for low-importance entries.

### Phase 3: High-Performance Vector Backends & Scalability (v0.3.0 — Medium Term)
- [ ] **Scalable Vector Stores**:
  - Optional adapters for FAISS, Qdrant, ChromaDB, and `pgvector`.
  - Persistent HNSW index support for high-throughput similarity search.
- [ ] **Hierarchical Context Summarization**:
  - Multi-level tree summarization for long-running conversations (100+ turns).
  - Fact extraction pipelines converting chat turns into structured entities/triples.
- [ ] **Multi-Agent Memory Sharing**:
  - Cross-agent memory scoping (shared team memory vs. private agent memory).
  - Role-based access control and namespace isolation.

### Phase 4: Enterprise & Production Readiness (v1.0.0 — Long Term)
- [ ] **Observability & Telemetry**:
  - OpenTelemetry integration for tracing memory retrieval and context packing latency.
  - Structured audit logging for compliance and memory inspection.
- [ ] **Production Storage Engines**:
  - PostgreSQL / Redis persistence adapters for distributed agent architectures.
- [ ] **GUI / Dashboard Inspector**:
  - Web UI / CLI tools for visual memory inspection, debugging, and manual editing.

---

## 💡 Feedback & Contributions

We welcome community feedback and contributions! If you have feature requests or ideas, please open an issue or discussion on the repository.

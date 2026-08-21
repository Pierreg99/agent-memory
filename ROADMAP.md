# Agent Memory Roadmap

This roadmap outlines the planned evolution and future directions for the `agent-memory` library.

---

## Short-Term (v0.2.0) — Core Developer Ergonomics

- [ ] **Async API Support (`AsyncAgentMemory`)**
  - Native `async`/`await` interfaces for all storage, summarization, and vector retrieval calls.
  - Async SQLite persistence engine via `aiosqlite`.
- [ ] **Import/Export Session Tools**
  - Methods to export and import entire agent conversation histories and vector stores to JSON/YAML files.
- [ ] **Custom System Message Formatting Templates**
  - Configurable string templates for rendering summaries and long-term facts in `MemoryPack.to_chat_messages()`.

---

## Mid-Term (v0.3.0) — Pluggable Storage & Vector Extensions

- [ ] **Additional Persistence Backends**
  - PostgreSQL / Supabase store plugin.
  - Redis store plugin for ultra-low latency context access.
- [ ] **External Vector Database Adapters**
  - Native integration with Qdrant, Chroma, and FAISS for scalable long-term memory retrieval.
- [ ] **Metadata Filtering & Hybrid Search**
  - Rich metadata filtering in `MemoryQuery` combined with keyword + semantic hybrid search.

---

## Long-Term (v1.0.0+) — Advanced Knowledge & Multimodal Memory

- [ ] **Knowledge Graph Memory Layer**
  - Entity-relationship extraction from conversations to build a structured knowledge graph alongside vector embeddings.
- [ ] **Multi-Modal Memory Support**
  - Token windowing and persistence support for image/audio/multimodal message entries.
- [ ] **Memory Decay & Consolidation**
  - Automatic time-based importance decay and background memory consolidation (dreaming/reflection cycles).

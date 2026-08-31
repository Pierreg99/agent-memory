# Agent Memory Roadmap

This document outlines the planned vision and development roadmap for `agent-memory`.

---

## 🎯 Short-Term (v0.2.0)

- [ ] **Async Support**: Native `async`/`await` methods for orchestrator, vector memory, and persistent store (`add_async`, `prepare_async`).
- [ ] **Expanded Vector Backends**: Built-in adapters for external vector databases (FAISS, Qdrant, ChromaDB, pgvector).
- [ ] **Enhanced Summarization**: Custom prompt template support and chunking for long conversations.
- [ ] **Memory Expiration & TTL**: Support time-to-live (TTL) and soft deletion for short-term and working memory entries.

---

## 🚀 Medium-Term (v0.3.0)

- [ ] **Multi-Session / Multi-Agent Graph**: Cross-session knowledge graph and shared entity memory across multiple agents.
- [ ] **Hierarchical Context Windows**: Support nested memory tiers (Working -> Short-term -> Medium-term -> Long-term).
- [ ] **Streaming Context Assembly**: Stream context packs directly into LLM completion APIs.
- [ ] **Automatic Knowledge Extraction**: Automatic background extraction of long-term facts from user turns.

---

## 🔮 Long-Term (v1.0.0)

- [ ] **Production Server Mode**: Optional standalone REST/gRPC memory microservice.
- [ ] **Plugin Ecosystem**: Custom pluggable indexers, embedding providers, and custom store drivers.
- [ ] **Benchmarking & Analytics**: Built-in evaluation metrics for context retrieval accuracy and compression ratios.

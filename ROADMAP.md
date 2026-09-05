# Roadmap

This roadmap outlines the planned evolution of `agent-memory`. The project aims to provide a lightweight, highly modular memory framework for LLM applications and agents.

---

## Short-Term (v0.2.0) — Async Support & Storage Enhancements

- [ ] **Async API Native Support**: Provide `AsyncAgentMemory` and async methods (`aadd_user`, `aprepare`, etc.) for high-concurrency frameworks (FastAPI, AsyncIO).
- [ ] **PostgreSQL / pgvector Persistence Provider**: Add an optional backend store for production deployments using PostgreSQL and `pgvector`.
- [ ] **Memory Decay & Expiration**: Implement time-based exponential decay for memory entry relevance scores and TTL support.
- [ ] **Hybrid Retrieval (BM25 + Dense Vectors)**: Combine sparse lexical keyword matching (BM25) with dense embeddings for improved recall accuracy.

---

## Medium-Term (v0.3.0) — Memory Structuring & Advanced Summarization

- [ ] **Graph-Based Memory & Knowledge Graphs**: Introduce entity-relation extraction to link facts into a graph structure for multi-hop reasoning.
- [ ] **Hierarchical & Progressive Summarization**: Support recursive, tree-structured conversation summaries for massive multi-session context lengths.
- [ ] **Qdrant & Chroma Vector Adapters**: Provide official vector database store integrations.
- [ ] **Redis Caching Layer**: Add optional Redis persistence for ultra-low latency prompt window construction.

---

## Long-Term (v1.0.0) — Production Readiness & Ecosystem Integration

- [ ] **Multi-Agent Memory Isolation & Sharing**: Configurable namespace policies for shared vs private agent memory workspaces.
- [ ] **LangChain, LlamaIndex, & AutoGen Adapters**: Plug-and-play middleware for popular agent orchestration frameworks.
- [ ] **Memory Inspector UI / CLI**: Interactive visualization tools to inspect, query, edit, and prune stored agent memories.
- [ ] **Comprehensive Benchmarks**: Standardized benchmark suite for latency, token budget efficiency, and memory retrieval precision/recall.

---

## Community Feedback & Contributing

We welcome community feedback on priorities! Feel free to open an issue or discussion on GitHub to request features or propose architectural extensions.

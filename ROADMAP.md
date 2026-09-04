# Project Roadmap

This document outlines planned features, subsystem enhancements, and long-term architectural goals for `agent-memory`.

---

## Short-Term (v0.2.0) — Expanded Adapters & Async Support

- [ ] **Async API Extensions**:
  - Add native `async` support to `AgentMemory` (`aadd_user`, `aprepare`, etc.) for high-concurrency agent execution frameworks (FastAPI, LangChain, AutoGen).
- [ ] **Redis & PostgreSQL Persistence Backends**:
  - Implement optional `RedisStore` and `PostgresStore` for distributed, multi-process persistent memory.
- [ ] **Enhanced Extractive Summarization**:
  - Add TF-IDF and LexRank extractive summarization algorithms as zero-dependency alternatives.
- [ ] **Expanded Tokenizer Support**:
  - Add support for Anthropic `claude-token-counter` and HuggingFace `tokenizers`.

---

## Medium-Term (v0.3.0) — Scalable Vector Backends & Memory Consolidation

- [ ] **External Vector Database Adapters**:
  - Add pluggable vector stores for production vector databases:
    - `QdrantVectorMemory`
    - `PgVectorMemory`
    - `FaissVectorMemory`
    - `ChromaVectorMemory`
- [ ] **Hierarchical Memory Consolidation**:
  - Periodic background consolidation of short-term chat turns into structured entity graphs and long-term facts.
- [ ] **Forgetting / Decay Mechanisms**:
  - Introduce exponential time-decay and importance degradation models for long-term facts.

---

## Long-Term (v1.0.0) — Enterprise Reliability & Advanced Analytics

- [ ] **Multi-Tenant Isolation**:
  - Built-in multi-tenant isolation with encrypted storage per session/user.
- [ ] **Memory Analytics Dashboard**:
  - Telemetry hooks and export utilities for token context utilization, summary quality metrics, and retrieval recall analysis.
- [ ] **Distributed Agent Syncing**:
  - Multi-agent memory synchronization protocols enabling shared agent state and sub-agent memory inheritance.

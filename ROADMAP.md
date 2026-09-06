# Agent Memory Roadmap

This document outlines the vision, development roadmap, and feature progress for **Agent Memory**.

---

## 📌 Project Vision & Principles

Agent Memory is designed to be a fast, modular, zero-lock-in memory subsystem for LLM agents.

- **Lightweight Core:** Minimal dependencies (`pydantic`, `numpy`, `pyyaml`, `requests`) with optional heavy extensions.
- **Pluggable Architecture:** Token counters, summarizers, vector embedders, and storage backends adhere to clear Protocols.
- **Deterministic & Auditable:** Clear context assembly, explicit token accounting, and session-safe isolation.
- **SDK Agnostic:** Outputs clean chat completions messages compatible with OpenAI, Anthropic, Ollama, and custom LLM interfaces.

---

## 🟢 Current Status: v0.1.1 (Released & Stable)

### Delivered Capabilities
- ✅ **Token-Aware Windowing:** `sliding`, `truncate_oldest`, and `summarize_old` strategies with response-token reservations.
- ✅ **Pluggable Token Counters:** `HeuristicTokenCounter` (zero-dependency) and `TiktokenTokenCounter` (exact token counting).
- ✅ **Resilient Summarization:** Fast extractive sentence-scoring by default, plus OpenAI-compatible `LLMSummarizer` with automatic extractive fallback on errors or missing keys (`ResilientSummarizer`).
- ✅ **RAG Long-Term Vector Memory:** Deterministic `HashEmbedder` and optional `SentenceTransformersEmbedder`. Session-isolated queries with metadata, kind, importance, and similarity filtering.
- ✅ **SQLite Persistence:** Per-thread connection handling for file-based or in-memory SQLite storage.
- ✅ **YAML Configuration:** Deep-merged configuration order (defaults -> `MEMORY_CONFIG_PATH` -> runtime `overrides`).
- ✅ **Quality & CI:** Fully typed Pydantic models, 100% passing test suite (63 tests), Python 3.10–3.13 support, clean `ruff` linting.

---

## 🎯 Future Milestones

### Phase 1: Core Enhancements (Near-term — v0.2.0)

- [ ] **Async API Support (`AsyncAgentMemory`)**
  - Non-blocking async persistence and vector queries for high-concurrency agent servers (FastAPI, asyncio event loops).
- [ ] **External Vector Store Backends**
  - Plug-and-play adapters for `pgvector`, `Qdrant`, and `ChromaDB` behind the `VectorMemory` protocol.
- [ ] **Advanced Token & Window Strategies**
  - Priority-weighted message retention and semantic chunking for long-turn conversations.
- [ ] **Memory Decay & TTL**
  - Importance decay over time or access frequency to keep vector retrieval sharp and relevant.

### Phase 2: Multi-Agent & Structured Knowledge (Mid-term — v0.3.0)

- [ ] **Multi-Agent Shared Memory**
  - Session and namespace permissions allowing multiple agents to read/write shared knowledge pools safely.
- [ ] **Graph & Hierarchical Memory**
  - Relationship links between memory entities (e.g. user preferences -> context -> related facts).
- [ ] **Hierarchical Summarization Trees**
  - Multi-tiered summarization for extremely long user sessions (summaries of summaries).
- [ ] **Observability & Inspection Hooks**
  - Exportable memory inspect/trace logs (OpenTelemetry or JSON logs) for agent debugging.

### Phase 3: Framework Ecosystem & Enterprise (Long-term — v1.0.0)

- [ ] **Framework Adapters**
  - Turnkey integration wrappers for LangChain, LlamaIndex, CrewAI, and AutoGen.
- [ ] **Enterprise Persistence Drivers**
  - PostgreSQL, Redis, and DynamoDB storage engines.
- [ ] **Self-Optimizing Memory**
  - Automatic dynamic tuning of window budgets and vector similarity thresholds based on conversation flow.

---

## 🤝 Feedback & Contributions

Suggestions, feature requests, and contributions are welcome! Please consult [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and open an issue or pull request on GitHub.

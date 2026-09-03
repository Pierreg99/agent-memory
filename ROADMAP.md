# Agent Memory Roadmap

This document outlines the strategic product vision, current status, and planned feature roadmap for `agent-memory`.

---

## 🎯 Vision & Guiding Principles

`agent-memory` aims to be the standard, lightweight memory layer for LLM agents in Python.

1. **Zero Mandatory Infrastructure**: Out-of-the-box defaults use zero external servers or heavy binary dependencies.
2. **Pluggable Architecture**: Every subsystem (token counting, context windowing, summarization, vector store, persistence) is defined by a Protocol and can be independently swapped.
3. **Type Safety & Reliability**: Pydantic models enforce strict validation across configuration and runtime state.
4. **LLM Agnostic**: Output standard python primitives and dictionaries (`MemoryPack.to_chat_messages()`) compatible with OpenAI, Anthropic, LangChain, LlamaIndex, or custom LLM clients.

---

## 📊 Current Status (v0.1.0)

- [x] **Orchestrator**: Unified `AgentMemory` class with intuitive session and turn ingestion APIs.
- [x] **Context Windowing**: Strategies for `sliding`, `truncate_oldest`, and `summarize_old`.
- [x] **Summarization**: `ExtractiveSummarizer` (frequency-based) and `LLMSummarizer` (OpenAI API) with automatic `ResilientSummarizer` fallback.
- [x] **Vector Memory**: `VectorMemory` with `HashEmbedder` and `SentenceTransformerEmbedder`, cosine similarity scoring, and metadata filtering.
- [x] **Persistence**: Thread-safe SQLite store supporting file-based or in-memory (`:memory:`) databases.
- [x] **Configuration**: YAML configuration with deep-merge dictionary overrides.
- [x] **Testing**: 100% pass rate across 48 unit and integration tests.

---

## 🚀 Near-Term Milestones (v0.2.0)

### ⚡ Async Support
- [ ] Add `AsyncAgentMemory` wrapper for non-blocking I/O in FastAPI / asyncio agent runtimes.
- [ ] Asynchronous SQLite persistence backend using `aiosqlite`.
- [ ] Async vector querying and LLM summarization calls.

### 🤖 Expanded Summarizer Adapters
- [ ] Direct Anthropic Claude adapter (`AnthropicSummarizer`).
- [ ] Local Ollama / vLLM summarizer adapter.
- [ ] Custom callable function support for summarizer injection.

### 🔍 Advanced Metadata Filtering
- [ ] Support numeric range filters (`$gt`, `$gte`, `$lt`, `$lte`).
- [ ] Support set membership filters (`$in`, `$nin`).
- [ ] Support boolean logic operators (`$and`, `$or`).

---

## 🔮 Mid-Term Milestones (v0.3.0 – v0.4.0)

### 🗄️ External Vector & Persistence Backends
- [ ] **Vector Stores**:
  - [ ] Qdrant adapter (`QdrantVectorMemory`).
  - [ ] ChromaDB adapter (`ChromaVectorMemory`).
  - [ ] FAISS in-memory index adapter.
  - [ ] PostgreSQL `pgvector` adapter.
- [ ] **Persistence Stores**:
  - [ ] PostgreSQL store adapter.
  - [ ] Redis store adapter for ultra-low latency caching.

### 🧹 Memory Lifecycle & Hygiene
- [ ] Time-to-Live (TTL) auto-expiration for temporary context and entries.
- [ ] Decay-based importance scoring (relevance diminishes over time unless reinforced).
- [ ] Deduplication pipeline for long-term facts.

### 🌊 Streaming & Token Accounting
- [ ] Token counter stream hook for counting tokens dynamically during stream generation.
- [ ] Real-time token usage reporting.

---

## 🏆 Long-Term Vision (v1.0.0)

### 🌐 Multi-Agent & Shared Memory
- [ ] Multi-agent memory namespaces with read/write access levels.
- [ ] Global organizational memory sharing across agent teams.
- [ ] Agent-to-agent context sync and memory transfer protocols.

### 🛠️ Developer Tooling & Inspection
- [ ] CLI tool `agent-memory inspect` to query and view memory stores, vector spaces, and context budgets.
- [ ] Web visualizer dashboard for inspecting active session contexts, summaries, and RAG retrievals in real time.

# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Async support (`AsyncAgentMemory`, async SQLite / vector storage).
- Advanced vector database adapters (FAISS, Qdrant, ChromaDB, PostgreSQL `pgvector`).
- Streaming token counters for real-time response generation.
- Expanded summarizer backends (Anthropic Claude, local Ollama models).

## [0.1.0] - 2025-01-15

### Added
- **Top-Level Orchestrator (`AgentMemory`)**:
  - Unifies context window management, summarization, long-term vector memory, and persistent storage.
  - Ergonomic helper methods: `add_user`, `add_assistant`, `add_system`, `add_long_term`, `prepare`, `stats`, `clear_session`.
  - Supports YAML-driven configuration with `from_config` and `from_yaml`.
- **Token-Aware Context Windowing (`WindowManager`)**:
  - Flexible window strategies: `sliding`, `truncate_oldest`, and `summarize_old`.
  - Token counting via `HeuristicTokenCounter` (zero-dependency) and `TiktokenTokenCounter` (optional).
- **Automatic Summarization Engine (`Summarizer`)**:
  - `ExtractiveSummarizer`: Keyword-frequency scoring for offline / local execution.
  - `LLMSummarizer`: OpenAI-compatible completions backend.
  - `ResilientSummarizer`: Auto-fallback from LLM to Extractive on error or missing API keys.
- **RAG Long-Term Memory (`VectorMemory`)**:
  - Dense retrieval with cosine similarity over `MemoryEntry` items.
  - Support for `HashEmbedder` (deterministic, zero-dependency) and `SentenceTransformerEmbedder` (optional).
  - Importance-based ranking and key-value metadata filtering.
- **Thread-Safe SQLite Persistence (`MemoryStore`)**:
  - Per-thread SQLite connections with automatic schema management.
  - Support for in-memory (`:memory:`) or persistent disk stores.
- **Data Models & Settings**:
  - Strongly typed Pydantic models (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`).
  - Hierarchical configuration settings via PyYAML with deep override merging.
- **Testing & Documentation**:
  - Complete test suite with 48 unit and integration tests.
  - End-to-end demo script (`examples/run_demo.py`).
  - Architecture specification in `docs/architecture.md`.

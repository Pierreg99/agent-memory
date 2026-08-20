# Changelog

All notable changes to the `agent-memory` library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-20

### Added
- **Core Orchestrator (`AgentMemory`)**:
  - Main top-level class orchestrating subsystems (`from_config()`, `from_yaml()`).
  - Helper methods for user, assistant, system, and long-term fact ingestion (`add_user`, `add_assistant`, `add_system`, `add_long_term`).
  - Context assembly via `prepare()` returning an LLM-ready `MemoryPack`.
  - Introspection support via `stats()` and session management via `clear_session()`.
- **Token Window Management**:
  - Pluggable token counters (`HeuristicTokenCounter` and optional `TiktokenTokenCounter`).
  - `WindowManager` supporting `sliding`, `truncate_oldest`, and `summarize_old` window strategies.
  - Automatic system prompt pinning and response token reservation.
- **Summarization Engine**:
  - `ExtractiveSummarizer` using sentence-level keyword frequency scoring without external LLM dependencies.
  - `LLMSummarizer` for OpenAI-compatible chat completion summarization.
  - `ResilientSummarizer` automatically falling back from LLM to extractive summarization on failure or missing API keys.
  - Auditable summaries tracking `source_message_ids`.
- **Vector Memory (RAG)**:
  - `VectorMemory` store with metadata filtering, similarity thresholding, and importance filtering.
  - `HashEmbedder` providing deterministic, dependency-free feature hashing over n-grams.
  - `SentenceTransformersEmbedder` adapter for optional dense embedding models.
- **Durable Persistence**:
  - `MemoryStore` backed by SQLite with per-thread connections and index optimizations.
  - Multi-session support with isolated message history, summaries, and long-term entries.
  - In-memory (`:memory:`) or disk-backed persistence modes.
- **Type Safety & Configuration**:
  - Pydantic models for data structures (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`).
  - YAML configuration (`defaults.yaml`) with deep-merging override support.
- **Examples & Docs**:
  - End-to-end multi-turn demo script (`examples/run_demo.py`).
  - Comprehensive architectural overview (`docs/architecture.md`).
  - Full test suite with unit and integration tests covering all subsystems.

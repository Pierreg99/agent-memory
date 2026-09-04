# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-19

### Added
- **Top-Level Orchestrator (`AgentMemory`)**: Unified manager composing context window management, summarization, long-term memory retrieval, and persistence.
- **Token-Aware Context Window**:
  - Token counting strategies (`HeuristicTokenCounter`, `TiktokenCounter`).
  - Context windowing strategies (`sliding`, `truncate_oldest`, `summarize_old`).
- **Pluggable Summarization**:
  - `ExtractiveSummarizer` for lightweight text compression.
  - `LLMSummarizer` adapter supporting OpenAI-compatible chat completion APIs.
- **RAG-Style Vector Memory**:
  - In-process cosine similarity store supporting metadata and importance filtering.
  - Pluggable embeddings (`HashEmbedder` and optional `SentenceTransformerEmbedder`).
- **SQLite Persistence**:
  - Thread-safe storage layer for conversation messages, summaries, and long-term memory entries.
- **YAML Configuration**:
  - Hierarchical YAML configuration with customizable overrides and Pydantic validation.
- **Documentation & CI**:
  - Complete architectural guide (`docs/architecture.md`).
  - Comprehensive unit and integration test suite (48 tests).
  - GitHub Actions workflow for automated PyPI publishing.

### Changed
- Refactored imports across vector, window, and test modules to adhere to strict `ruff` linting standards.

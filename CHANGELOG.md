# Changelog

All notable changes to `agent-memory` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Roadmap and future milestones section in `README.md`.
- Project changelog (`CHANGELOG.md`).

### Fixed
- Fixed command example path in `examples/run_demo.py` docstring.

## [0.1.0] - 2026-08-19

### Added
- **Top-level Orchestrator (`AgentMemory`)**: High-level interface managing token budgeting, context packing, automatic summarization, RAG recall, and persistence.
- **Context Window Management (`WindowManager`)**: Support for sliding window, truncate-oldest, and summarize-old window strategies.
- **Token Counters (`TokenCounter`)**: Fast `HeuristicTokenCounter` with token estimation and optional `TiktokenTokenCounter` adapter for exact counting.
- **Pluggable Summarizer (`Summarizer`)**: Extractive keyword-scoring summarizer (`ExtractiveSummarizer`), OpenAI-compatible LLM summarizer (`LLMSummarizer`), and error-resilient composite (`ResilientSummarizer`).
- **Vector Memory & RAG (`VectorMemory`)**: In-process similarity search supporting deterministic feature hashing (`HashEmbedder`) and optional `sentence-transformers` models.
- **Persistence Layer (`MemoryStore`)**: SQLite storage for chat messages, summaries, and long-term memory facts with thread-safe connection handling.
- **Pydantic Data Models**: Strongly-typed `Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`, and YAML-driven `MemorySettings`.
- **Testing & Documentation**: Unit and integration test suite covering orchestrator, windowing, summarization, vector recall, and persistence.

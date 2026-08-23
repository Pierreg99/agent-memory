# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-19

### Added
- **Orchestration Layer (`AgentMemory`)**: High-level unified interface for managing LLM agent memory, token budgets, summarization, and retrieval.
- **Context Window Manager (`WindowManager`)**: Support for `sliding`, `truncate_oldest`, and `summarize_old` strategies to maintain context under strict token ceilings.
- **Token Counters**: Heuristic token counter with zero external dependencies and optional `tiktoken` adapter support.
- **Summarization Subsystem**: Extractive summarizer by default and resilient LLM-compatible summarization fallback adapters.
- **RAG-style Vector Memory**: Similarity search with deterministic hash embedding adapter by default and optional `sentence-transformers` integration.
- **SQLite Persistence (`MemoryStore`)**: Thread-safe per-thread SQLite store for messages, summaries, and long-term facts.
- **Pydantic Data Models**: Strongly-typed structures (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`, `MemorySettings`).
- **Comprehensive Test Suite & Examples**: 48 unit and integration tests and end-to-end runnable demo (`examples/run_demo.py`).
- **Automation**: GitHub Actions workflow for PyPI packaging and publishing.

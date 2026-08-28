# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-15

### Added
- **Core Orchestration**: Introduced `AgentMemory` orchestrator class with YAML configuration loading and top-level prompt preparation (`prepare()`).
- **Context Window Management**: Token-aware context windowing with `sliding`, `truncate_oldest`, and `summarize_old` strategies.
- **Pluggable Token Counting**: Heuristic token counter default with optional `tiktoken` adapter support.
- **Summarization Subsystem**: Extractive summarizer default and OpenAI-compatible LLM summarizer with graceful fallback.
- **RAG / Vector Memory Store**: Long-term memory store supporting deterministic hash embeddings and optional `sentence-transformers` embeddings.
- **Persistence Layer**: Thread-safe SQLite storage for chat history and long-term memory entries (in-memory or file-backed).
- **Data Models & Types**: Pydantic models (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`) and enums for safe type validation.
- **CI/CD Workflow**: GitHub Actions workflow for Python package publishing to PyPI.
- **Test Suite**: Comprehensive test suite covering configuration, window management, summarization, vector memory, persistence, and orchestrator functions.

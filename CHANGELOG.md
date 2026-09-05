# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Cleaned up imports and formatting across `agent_memory`, `tests/`, and `examples/`.
- Fixed execution path instructions in `examples/run_demo.py`.

## [0.1.0] - 2026-08-19

### Added
- **Orchestrator**: `AgentMemory` class providing unified memory context management for LLM agents.
- **Context Windowing**: Token-aware sliding, oldest turn truncation, and automatic summarization strategies (`WindowManager`).
- **Token Counters**: Heuristic counter with character-based estimation and optional `tiktoken` integration (`TokenCounter`).
- **Summarization**: Extractive sentence-ranking summarizer and resilient LLM summarization fallback (`ResilientSummarizer`, `ExtractiveSummarizer`).
- **Vector Store (RAG)**: In-process cosine similarity RAG store supporting metadata filters and importance scoring (`VectorMemory`).
- **Persistence**: Thread-safe SQLite storage for short-term conversation logs and long-term memory entries (`MemoryStore`).
- **Configuration**: Deep-merging YAML configuration loading via `agent_memory/config/defaults.yaml` and Pydantic settings.
- **CI/CD Workflow**: GitHub Actions workflow for automated PyPI publishing on release creation.
- **Tests & Demo**: Comprehensive test suite covering units and integration, plus runnable end-to-end example (`examples/run_demo.py`).

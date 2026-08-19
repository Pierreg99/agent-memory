# Changelog

All notable changes to the `agent-memory` library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed context window manager minimum floor (`keep_last_turns`) enforcement when total tokens exceed budget in sliding strategy.
- Improved metadata handling in `AgentMemory.add_user()`, `add_assistant()`, and `add_system()` to accept explicit `metadata` dictionaries alongside keyword arguments without nested structures.
- Corrected execution command path in `examples/run_demo.py` docstring.

### Added
- Comprehensive project `ROADMAP.md` tracking completed core features, active progress, and future development milestones.
- Standardized `CHANGELOG.md` for tracking project evolution.

## [0.1.0] - 2025-01-15

### Added
- **Core Orchestration**: `AgentMemory` top-level class composing token counting, windowing, summarization, vector recall, and persistence.
- **Token Counting**: `HeuristicTokenCounter` (character-based estimation) and optional `TiktokenTokenCounter` adapter.
- **Context Window Management**: `WindowManager` supporting `sliding`, `truncate_oldest`, and `summarize_old` strategies with response token reservation and system prompt pinning.
- **Summarization Subsystem**: `ExtractiveSummarizer` (keyword frequency heuristic) and `ResilientSummarizer` / `LLMSummarizer` (OpenAI-compatible chat completion with fallback).
- **RAG / Vector Memory**: `VectorMemory` with deterministic `HashEmbedder` and optional `SentenceTransformersEmbedder` adapter, supporting kind, importance, and metadata filtering.
- **Durable Persistence**: `MemoryStore` backed by thread-safe SQLite (in-memory or file path) for chat messages, summaries, and long-term memory entries.
- **YAML Configuration**: `MemorySettings` Pydantic models with deep-merge support via `load_settings()`.

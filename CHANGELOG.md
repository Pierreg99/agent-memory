# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Created `CHANGELOG.md`, `PROGRESS.md`, and `ROADMAP.md` to document project evolution, implementation progress, and future milestones.

---

## [0.1.0] - 2026-08-19

### Added
- **Top-Level Orchestrator (`AgentMemory`)**: Single public entry point wiring context window management, summarization, long-term memory (RAG), and persistence together.
- **Token-Aware Context Window**: Sliding, truncate-oldest, and summarize-old windowing strategies with configurable token budgets and response token reservations.
- **Pluggable Token Counters**: Built-in `HeuristicTokenCounter` with character-to-token heuristic and caching; optional `TiktokenCounter` adapter.
- **Summarization Subsystem**: Extractive heuristic summarizer and OpenAI-compatible `LLMSummarizer` fallback adapter with source turn tracing (`source_message_ids`).
- **Vector & RAG Memory**: Long-term recall engine powered by `HashEmbedder` (deterministic feature hashing) or optional `SentenceTransformerEmbedder`.
- **Durable Persistence**: SQLite-backed store with thread-local connection management, session isolation, and in-memory or disk-backed databases.
- **Configuration Engine**: Deep-merging YAML configurationloader backed by validated Pydantic settings models (`MemorySettings`).
- **Testing & Quality**: 48 unit and integration tests covering all subsystems and core models with 100% test suite pass rate.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-19

### Added

- **Modular Architecture**: Built an end-to-end memory layer orchestrator (`AgentMemory`) supporting pluggable subsystems.
- **Context Window Management**: Token-aware sliding window, truncate oldest, and summarize old context management strategies (`WindowManager`).
- **Token Counter Implementations**: Pluggable `HeuristicTokenCounter` (zero-dependency default) and optional `TiktokenCounter` adapter (`TokenCounter`).
- **Summarization Subsystem**: Extractive heuristic summarizer (`ExtractiveSummarizer`) and OpenAI-compatible LLM adapter (`LLMSummarizer`).
- **Long-term Vector Memory (RAG)**: In-process cosine similarity retrieval with metadata filtering (`VectorMemory`), supported by `HashEmbedder` and optional `SentenceTransformerEmbedder`.
- **Durable Persistence**: Thread-safe SQLite store (`MemoryStore`) supporting in-memory or on-disk storage with per-thread connection safety.
- **YAML Configuration**: Hierarchical configuration management driven by `defaults.yaml` and Pydantic models with override capabilities.
- **CI/CD & Publishing**: GitHub Actions workflows for Python package testing and automated PyPI publishing.

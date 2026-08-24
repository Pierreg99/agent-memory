# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-19

### Added
- **Top-Level Orchestrator (`AgentMemory`)**: High-level interface for ingesting turns, storing long-term recall facts, preparing LLM context packs (`MemoryPack`), and inspecting session statistics.
- **Context Window Management**: Supports `sliding`, `truncate_oldest`, and `summarize_old` window strategies with configurable token ceilings, response reserves, and turn-retention limits.
- **Token Counting**: Fast heuristic token estimator (`HeuristicTokenCounter`) and optional `tiktoken` counter (`TiktokenTokenCounter`) with token count caching.
- **Automatic Summarization**: Extractive sentence keyword scoring (`ExtractiveSummarizer`) and OpenAI-compatible LLM summarizer (`LLMSummarizer`) with automatic fallback (`ResilientSummarizer`).
- **Vector Memory (RAG)**: In-process vector store supporting deterministic feature hashing (`HashEmbedder`) and optional `sentence-transformers` embeddings (`SentenceTransformersEmbedder`) with similarity and importance filtering.
- **SQLite Persistence**: Thread-safe database store (`MemoryStore`) supporting ephemeral in-memory databases and file-backed persistent storage.
- **Configuration Engine**: YAML-driven configuration loader supporting default settings and deep-merged dictionary overrides.
- **Demo & Tests**: Complete end-to-end example (`examples/run_demo.py`) and 48 pytest unit and integration tests.

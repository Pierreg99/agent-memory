# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-19

### Added

- **AgentMemory Orchestrator**: Core API (`AgentMemory`) supporting top-level memory management, adding system/user/assistant messages, managing long-term memories, and preparing memory context packages for LLMs (`MemoryPack`).
- **Context Window Management**: Token-aware context windowing with flexible strategies (`sliding`, `truncate_oldest`, `summarize_old`).
- **Pluggable Token Counters**: Support for heuristic word/character token estimation and `tiktoken` encoding adapter.
- **Pluggable Summarizers**: Extractive summarization backend and OpenAI-compatible LLM summarization adapter with graceful fallback handling and turn traceability.
- **Vector Long-Term Memory (RAG)**: In-memory/vector store supporting deterministic hashing embeddings (`HashEmbedder`) and optional `sentence-transformers` models (`SentenceTransformerEmbedder`).
- **SQLite Persistence**: Thread-safe persistent storage (`SQLiteMemoryStore`) using thread-local connections for cross-session storage.
- **YAML Configuration System**: Hierarchical configuration loaded from `agent_memory/config/defaults.yaml` with support for programmatic deep-merge overrides.
- **Pydantic Data Models**: Statically typed data models (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`, `TokenCount`) for error prevention at system boundaries.
- **Test Suite**: Complete test suite with 48 unit and integration tests covering models, window management, token counting, summarization, vector retrieval, persistence, and end-to-end orchestration.
- **Examples**: Included runnable end-to-end demo script (`examples/run_demo.py`).
- **Documentation**: Initial architectural documentation (`docs/architecture.md`) and project `README.md`.

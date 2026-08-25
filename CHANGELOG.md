# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Created `CHANGELOG.md` to track project releases and changes over time.
- Created `ROADMAP.md` detailing future developmental milestones (Async support, Vector DB adapters, Hierarchical summarization, Telemetry).
- Created `PROGRESS.md` documenting current implementation status, test metrics, and component readiness.

### Fixed
- Fixed execution path in `examples/run_demo.py` docstring header to point to correct relative paths (`PYTHONPATH=. python examples/run_demo.py`).
- Proofread and polished documentation references across `README.md` and `docs/architecture.md`.

## [0.1.0] - 2026-08-19

### Added
- Initial public release of `agent-memory`.
- **Context Window Management**: Sliding, truncate-oldest, and summarize-old windowing strategies.
- **Token Counter Subsystem**: Fast heuristic token estimator and optional `tiktoken` integration.
- **Summarization Subsystem**:
  - `ExtractiveSummarizer` using sentence keyphrase scoring.
  - `LLMSummarizer` connecting to OpenAI-compatible chat endpoints.
  - `ResilientSummarizer` automatic fallback mechanism.
- **Vector Memory (RAG)**:
  - In-process vector store supporting cosine similarity and importance/metadata filtering.
  - Deterministic `HashEmbedder` (zero external dependencies).
  - Optional `SentenceTransformersEmbedder` adapter.
- **SQLite Persistence Store**:
  - Per-thread SQLite connection management for thread safety.
  - Persistent message logs, summaries, and long-term memory entries.
- **Type Safety & Configuration**:
  - Pydantic v2 data models (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`).
  - Deep-mergeable YAML configuration driven by `defaults.yaml`.
- **CI/CD Workflow**:
  - GitHub Actions publishing workflow for PyPI releases.

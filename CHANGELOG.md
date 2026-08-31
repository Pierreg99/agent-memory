# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-20

### Added
- Modular, YAML-driven agent memory system (`AgentMemory`).
- Token-aware context windowing with `sliding`, `truncate_oldest`, and `summarize_old` strategies.
- Token counters with `HeuristicTokenCounter` and optional `TiktokenTokenCounter`.
- Summarization engine with `ExtractiveSummarizer` (keyword frequency) and `ResilientSummarizer` (LLM with extractive fallback).
- In-process vector memory for long-term fact recall with `HashEmbedder` and `SentenceTransformersEmbedder`.
- Persistent SQLite storage (`MemoryStore`) with auto-schema setup and thread safety.
- Full Pydantic data models (`Message`, `MemoryEntry`, `MemoryQuery`, `MemoryPack`).
- Comprehensive unit and integration test suite with 50+ test cases.

### Fixed
- Fixed `keep_last_turns` minimum floor logic in `WindowManager._sliding`.
- Fixed metadata parameter merging when calling `add_user`, `add_assistant`, and `add_system`.
- Added query input validation in `VectorMemory` for empty strings and invalid `top_k`.

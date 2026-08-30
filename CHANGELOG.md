# Changelog

All notable changes to the `agent-memory` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Initial Release

### Added
- **Token-Aware Context Windowing**: Supports `sliding`, `truncate_oldest`, and `summarize_old` window management strategies.
- **Token Counting**: Includes heuristic tokenizer by default with optional `tiktoken` support for precise token counting.
- **Pluggable Summarization**: Built-in extractive summarizer and optional OpenAI-compatible LLM summarizer with graceful fallback error handling.
- **RAG-style Long-Term Memory**: Vector memory layer using hash-based embeddings by default or optional `sentence-transformers`.
- **SQLite Persistence**: Thread-safe database storage supporting both in-memory (`:memory:`) and file-backed SQLite connections.
- **Pydantic Data Models & Config**: Full type validation with Pydantic and deep-merged YAML configuration defaults.
- **CI/CD Integration**: GitHub Actions workflow for building and publishing packages to PyPI upon release creation.
- **Comprehensive Test Suite**: 48 unit and integration tests covering all core modules and edge cases.

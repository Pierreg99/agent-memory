# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-09-05

### Fixed

- `VectorMemory.query` now filters by `MemoryQuery.session_id`, preventing
  cross-session fact leakage in multi-tenant usage.
- `AgentMemory.clear_session` clears only that session’s vector entries
  via `VectorMemory.clear_session` instead of wiping the entire store.

### Added

- `MEMORY_CONFIG_PATH` support in `load_settings` / `from_config`
  (deep-merged over packaged defaults; overrides still win).
- Clearer validation errors for invalid roles, empty message content,
  unknown window/summary/vector backends, and missing YAML paths.
- CI workflow (`.github/workflows/ci.yml`) running pytest on Python
  3.10–3.13 plus a packaging import smoke job.
- Documentation suite: refreshed README and architecture notes; new
  `docs/api.md`, `docs/config.md`, `docs/cookbook.md`; `CHANGELOG.md`,
  `CONTRIBUTING.md`; optional static `docs/index.html`.
- Gap-filling tests for session isolation, metadata filters, config env,
  YAML loading, resilient summarizer fallback, and store helpers.

### Changed

- Package metadata: author `Pierreg99 <pierre@cryopg.it>`, project URLs,
  Python 3.13 classifier, optional `all` extra.
- Example demo docstring path corrected to `examples/run_demo.py`.
- README Status: ship-complete after PR #25 merge (63 tests green).

## [0.1.0] — 2026-09-05

### Added

- Initial `agent-memory` library: token-aware windowing, summarization,
  vector recall, SQLite persistence, YAML config, and `MemoryPack` chat
  export helpers.

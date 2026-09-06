# Agent Memory

A modular, configurable Python library that gives LLM agents a memory layer:
token-aware context windowing, automatic summarization, RAG-style long-term
recall, and durable persistence behind a small public API.

The resulting `MemoryPack` can be handed to OpenAI, Anthropic, or any
chat-completions-compatible SDK via `pack.to_chat_messages()`.

## Quick start

```bash
pip install agent-memory
```

```python
from agent_memory import AgentMemory

mem = AgentMemory.from_config({
    "persistence": {"sqlite_path": "./agent_mem.db"},
    "vector": {"persist_embeddings": True},
})
mem.add_system("You are a helpful assistant.")
mem.add_user("Hi! I'm Alice and I love hiking.")
mem.add_long_term("User's name is Alice", importance=0.9)
mem.add_long_term("User enjoys hiking", importance=0.7)

pack = mem.prepare("What do you know about me?", system_prompt="You are helpful.")
messages = pack.to_chat_messages()
mem.close()
```

## Features

- **Token-aware context window** — sliding, truncate-oldest, and summarize-old strategies with response-token reservation and a final hard prompt-budget check.
- **Pluggable summarizer** — extractive by default; OpenAI-compatible LLM adapter with deterministic fallback.
- **RAG-style long-term memory** — deterministic hash embeddings by default; optional `sentence-transformers`; session and metadata filtering.
- **Durable semantic recall** — vectors and their metadata can be persisted in SQLite and rehydrated after process restart.
- **SQLite persistence** — thread-local connections, automatic rollback on errors, session clearing, retention purge, and JSON-serializable export.
- **Typed public surface** — Pydantic models validate memory importance, query limits, and token counts.
- **Multilingual extraction** — extractive summaries tolerate Unicode and German sentence structure.

## Configuration

Behavior is YAML-driven. Resolution order for `AgentMemory.from_config`:

1. packaged `agent_memory/config/defaults.yaml`
2. optional `MEMORY_CONFIG_PATH` file (deep-merged)
3. `overrides` argument (highest precedence)

| Area | Key knobs |
|------|-----------|
| Window | `strategy`, `max_tokens`, `keep_last_turns`, `reserve_for_response` |
| Tokens | `backend`, `tiktoken_encoding`, `chars_per_token` |
| Summary | `backend`, trigger / budget thresholds, LLM settings |
| Vector | `enabled`, `backend`, `top_k`, `min_similarity`, `persist_embeddings` |
| Persistence | `enabled`, `sqlite_path`, `auto_commit` |
| Retention | `enabled`, `days`, `run_on_start` |
| Session | `default_id`, `clear_on_start` |

## Public API

| Call | Purpose |
|------|---------|
| `AgentMemory.from_config(overrides?)` | Build from defaults + overrides |
| `AgentMemory.from_yaml(path)` | Build from YAML |
| `add_user` / `add_assistant` / `add_system` | Ingest turns |
| `add_long_term` / `add_many_long_term` | Store durable facts |
| `prepare(query_text, …)` | Assemble a budget-fitted `MemoryPack` |
| `MemoryPack.to_chat_messages()` | OpenAI-style messages list |
| `export_session()` | Export one session as JSON-serializable data |
| `clear_session()` | Delete one session across all memory layers |
| `purge_expired()` | Apply the configured retention policy |
| `stats()` / `close()` | Introspection and cleanup |

## Layout

```text
agent_memory/                # Library package
├── agent_memory.py          # Orchestrator + lifecycle + budget fitting
├── core/                    # Pydantic models + enums
├── config/                  # settings + packaged defaults
├── window/                  # token counter + window manager
├── summary/                 # extractive + LLM summarizers
├── vector/                  # embedders + in-process vector index
└── persistence/             # SQLite store + persisted embeddings

tests/                       # Unit + integration + hardening tests
benchmarks/                  # Reproducible local benchmarks
docs/                        # Architecture, API, config, cookbook, reports
SECURITY.md                  # Security and privacy guidance
```

## Tests and benchmark

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
PYTHONPATH=. python benchmarks/run_memory_bench.py
```

CI runs the suite on Python 3.10–3.13 and performs a packaging/import smoke
test. fileciteturn10file0L2-L2

## Documentation

| Doc | Contents |
|-----|----------|
| `docs/architecture.md` | Data flow, design choices, extension points |
| `docs/api.md` | Public classes and methods |
| `docs/config.md` | Configuration reference |
| `docs/cookbook.md` | Practical recipes |
| `docs/reports/` | German/English architecture, production, security and evaluation reports |
| `SECURITY.md` | Security and privacy guidance |
| `CHANGELOG.md` | Release history |

## Status

**v0.2.0 — reliability and production hardening**

The release adds durable vector rehydration, lifecycle/retention helpers,
strict final prompt-budget fitting, summary coverage protection, multilingual
extractive summarization, stronger model validation, benchmarks, and security
privacy guidance.

## License

MIT — see [LICENSE](LICENSE).

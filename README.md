# Agent Memory

A modular, configurable Python library that gives any LLM agent a real
memory layer: token-aware context windowing, automatic summarization,
RAG-style long-term recall, and durable persistence — driven by YAML
config and a small public API.

Hand the resulting `MemoryPack` to OpenAI, Anthropic, or any
chat-completions-compatible SDK via `pack.to_chat_messages()`.

## Quick start

```bash
pip install agent-memory
# or from a clone:
# pip install -e ".[dev]"
```

```python
from agent_memory import AgentMemory

mem = AgentMemory.from_config()  # packaged defaults
mem.add_system("You are a helpful assistant.")
mem.add_user("Hi! I'm Alice and I love hiking.")
mem.add_long_term("User's name is Alice", importance=0.9)
mem.add_long_term("User enjoys hiking", importance=0.7)

pack = mem.prepare(
    "What do you know about me?",
    system_prompt="You are helpful.",
)

# Hand to any OpenAI-style chat API
messages = pack.to_chat_messages()
for cm in messages:
    print(cm["role"], "::", cm["content"][:80])
```

Override knobs without touching files:

```python
mem = AgentMemory.from_config({
    "window": {"max_tokens": 8000, "strategy": "summarize_old"},
    "summary": {"backend": "llm"},
    "vector": {"top_k": 5},
    "persistence": {"sqlite_path": "./agent_mem.db"},
})
```

Or load a YAML file:

```python
mem = AgentMemory.from_yaml("my_memory.yaml")
```

## Features

- **Token-aware context window** — `sliding`, `truncate_oldest`, and
  `summarize_old` strategies with response-token reservation.
- **Pluggable summarizer** — extractive by default; OpenAI-compatible LLM
  adapter with automatic extractive fallback on missing keys or network errors.
- **RAG-style long-term memory** — deterministic hash embeddings by default;
  optional `sentence-transformers`. Queries are filtered by session, kind,
  importance, metadata, and similarity.
- **SQLite persistence** — per-thread connections; `:memory:` or file path.
- **Thread-safe ingest path**, dependency-light core (`pydantic`, `numpy`,
  `pyyaml`, `requests`). Optional: `tiktoken`, `sentence-transformers`.
- **Typed public surface** — Pydantic models for messages, entries, queries,
  and the assembled `MemoryPack`.

## Installation

```bash
pip install agent-memory

# Optional extras
pip install "agent-memory[tiktoken]"
pip install "agent-memory[sentence-transformers]"
pip install "agent-memory[all]"
```

From source:

```bash
git clone https://github.com/Pierreg99/agent-memory.git
cd agent-memory
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

All behavior is YAML-driven. Resolution order for `AgentMemory.from_config`:

1. Packaged [`agent_memory/config/defaults.yaml`](agent_memory/config/defaults.yaml)
2. Optional env file via `MEMORY_CONFIG_PATH` (deep-merged)
3. The `overrides` dict argument (highest precedence)

| Area | Key knobs |
|------|-----------|
| Window | `strategy`, `max_tokens`, `keep_last_turns`, `reserve_for_response` |
| Tokens | `backend` (`heuristic` \| `tiktoken`), `chars_per_token` |
| Summary | `backend` (`extractive` \| `llm`), trigger / budget thresholds |
| Vector | `enabled`, `backend` (`hash` \| `sentence_transformers`), `top_k` |
| Persistence | `enabled`, `sqlite_path`, `auto_commit` |
| Session | `default_id` |

Full reference: [docs/config.md](docs/config.md).

## Public API (short)

| Call | Purpose |
|------|---------|
| `AgentMemory.from_config(overrides?)` | Build from defaults + overrides |
| `AgentMemory.from_yaml(path)` | Build from a YAML file |
| `add_user` / `add_assistant` / `add_system` | Ingest turns |
| `add_long_term` / `add_many_long_term` | Store RAG facts |
| `prepare(query_text, …)` | Assemble a `MemoryPack` |
| `MemoryPack.to_chat_messages()` | OpenAI-style messages list |
| `stats()` / `clear_session()` | Introspection and cleanup |

Details: [docs/api.md](docs/api.md). Patterns: [docs/cookbook.md](docs/cookbook.md).

## Layout

```
agent_memory/                # Library package
├── agent_memory.py          # Orchestrator (AgentMemory)
├── core/                    # Message, MemoryEntry, MemoryPack, enums
├── config/                  # defaults.yaml + MemorySettings
├── window/                  # Token counter + window manager
├── summary/                 # Extractive + LLM summarizers
├── vector/                  # Embeddings + VectorMemory
└── persistence/             # SQLite MemoryStore

tests/                       # Unit + integration tests
examples/run_demo.py         # Runnable multi-turn demo
docs/                        # Architecture, API, config, cookbook
```

Design notes: [docs/architecture.md](docs/architecture.md).

## Demo

```bash
PYTHONPATH=. python examples/run_demo.py
```

Tiny budgets are used on purpose so summarization and retrieval fire quickly.
No external LLM call is made; the reply is stubbed.

## Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

CI runs the suite on Python 3.10–3.13 (see `.github/workflows/ci.yml`).

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/architecture.md](docs/architecture.md) | Data flow, design choices, extension points |
| [docs/api.md](docs/api.md) | Public classes and methods |
| [docs/config.md](docs/config.md) | Every config field and default |
| [docs/cookbook.md](docs/cookbook.md) | Practical recipes |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup and PR expectations |

Optional static overview (local): open [`docs/index.html`](docs/index.html)
in a browser.

## Status

**Ship-complete · v0.1.1** (PR #25 merged)

- Session-safe vector memory, CI on Python 3.10–3.13, immersive docs suite.
- Local pytest: 63 passed.
- Docs: architecture, API, config, cookbook, optional `docs/index.html`.

## License

MIT — see [LICENSE](LICENSE).

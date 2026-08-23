# Agent Memory

A modular, configurable Python library that gives any LLM agent a real
memory layer: token-aware context windowing, automatic summarization,
RAG-style long-term recall, and durable persistence — all driven by
YAML config.

## Quick start

```python
from agent_memory import AgentMemory

mem = AgentMemory.from_config()        # loads defaults
mem.add_system("You are a helpful assistant.")
mem.add_user("Hi! I'm Alice and I love hiking.")
mem.add_long_term("User's name is Alice", importance=0.9)
mem.add_long_term("User enjoys hiking", importance=0.7)

pack = mem.prepare(
    "What do you know about me?",
    system_prompt="You are helpful.",
)

# Hand `pack.to_chat_messages()` to OpenAI / Anthropic / any LLM SDK.
for cm in pack.to_chat_messages():
    print(cm["role"], "::", cm["content"][:80])
```

## Features

- **Token-aware context window** with sliding, truncate-oldest, and
  summarize-old strategies.
- **Pluggable summarizer** — extractive by default, OpenAI-compatible
  LLM adapter available, falls back gracefully on errors.
- **RAG-style long-term memory** with pluggable embeddings (deterministic
  hash by default, optional `sentence-transformers`).
- **SQLite persistence** — per-thread connections, file or in-memory.
- **Thread-safe**, **dependency-light** (only `pydantic`, `numpy`,
  `pyyaml`, `requests` are required; `tiktoken` and `sentence-transformers`
  are optional).
- **Fully tested** — 48 unit + integration tests covering every module.

## Layout

```
agent_memory/                # Library package
├── __init__.py
├── agent_memory.py          # Top-level orchestrator (AgentMemory class)
├── core/                    # Pydantic data models
│   ├── models.py            #   Message, MemoryEntry, MemoryQuery, MemoryPack
│   └── types.py             #   Enums (Role, MemoryKind, WindowStrategy, ...)
├── config/                  # YAML config + Pydantic settings
│   ├── defaults.yaml
│   └── settings.py
├── window/                  # Token counter + context window manager
│   ├── token_counter.py
│   └── window_manager.py
├── summary/                 # Extractive + LLM summarizers
│   └── summarizer.py
├── vector/                  # Embeddings + RAG store
│   ├── embeddings.py
│   └── memory.py
└── persistence/             # SQLite store
    └── store.py

tests/                       # 48 unit + integration tests
examples/                    # Runnable end-to-end demo
docs/architecture.md         # Detailed design notes
```

## Installation

```bash
pip install agent-memory
```

Or from a local clone:

```bash
git clone https://github.com/Pierreg99/agent-memory.git
cd agent-memory
pip install -e .
```

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
# 48 passed
```

## Configuration

All behavior is YAML-driven. Override individual fields by passing a
dict to `AgentMemory.from_config(...)`:

```python
mem = AgentMemory.from_config({
    "window": {"max_tokens": 8000, "strategy": "summarize_old"},
    "summary": {"backend": "llm"},
    "vector": {"top_k": 5},
})
```

See `agent_memory/config/defaults.yaml` for the full list of knobs and
`docs/architecture.md` for the design rationale.

## Project Progress & Roadmap

- See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
- See [ROADMAP.md](ROADMAP.md) for planned features and future directions.

## Demo

```bash
PYTHONPATH=. python examples/run_demo.py
```

## License

MIT — see `LICENSE`.

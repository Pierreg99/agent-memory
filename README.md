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

## Project Progress & Status

| Module | Status | Highlights |
|---|---|---|
| **Orchestrator** | Complete | Unified `AgentMemory` facade, multi-turn state packing |
| **Windowing & Budgeting** | Complete | Token budgeting, sliding / truncate / summarize-old strategies |
| **Summarization** | Complete | Fast extractive keyword scoring + resilient LLM fallback |
| **RAG Vector Memory** | Complete | In-process cosine similarity, feature hashing, sentence-transformers |
| **Persistence** | Complete | Thread-safe SQLite store for messages, summaries, and facts |
| **Configuration** | Complete | YAML default configs with runtime dict overrides |

See [CHANGELOG.md](CHANGELOG.md) for detailed release history and updates.

## Roadmap

Future developments planned for `agent-memory`:

- **v0.2.0 - External Vector Store Integrations**
  - Adapters for ChromaDB, Qdrant, and FAISS for large-scale embedding search.
- **v0.3.0 - Advanced Memory Consolidation & Decay**
  - Automatic memory decay / pruning based on access frequency and time recency.
  - Hierarchical summarization tree for ultra-long conversations.
- **v0.4.0 - Async & Streaming Support**
  - Async persistence methods (`aio-sqlite`) and non-blocking LLM summarizer calls.
- **v0.5.0 - Multi-Tenant Memory Isolation & Access Control**
  - First-class support for multi-user session management and scoping permissions.

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

## Demo

```bash
PYTHONPATH=. python examples/run_demo.py
```

## License

MIT — see `LICENSE`.

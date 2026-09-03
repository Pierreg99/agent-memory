# Agent Memory

A modular, configurable Python library that gives any LLM agent a real
memory layer: token-aware context windowing, automatic summarization,
RAG-style long-term recall, and durable persistence — all driven by
YAML config.

## 🚀 Quick start

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

## ✨ Features

- **Token-aware context window** with `sliding`, `truncate_oldest`, and `summarize_old` strategies.
- **Pluggable summarizer** — extractive keyword-scoring by default, OpenAI-compatible LLM adapter available, falls back gracefully on errors.
- **RAG-style long-term memory** with pluggable embeddings (deterministic hash by default, optional `sentence-transformers`).
- **SQLite persistence** — thread-safe per-thread connections, file or in-memory.
- **Thread-safe & dependency-light** (only `pydantic`, `numpy`, `pyyaml`, `requests` required; `tiktoken` and `sentence-transformers` optional).
- **Fully tested** — 48 unit + integration tests covering every module.

## 📊 Component Progress & Status

| Subsystem | Component | Default Implementation | Status |
|---|---|---|---|
| **Orchestrator** | `AgentMemory` | Top-level pipeline orchestrator | ✅ Production Ready |
| **Context Window** | `WindowManager` | `sliding`, `truncate_oldest`, `summarize_old` | ✅ Production Ready |
| **Token Counter** | `TokenCounter` | `HeuristicTokenCounter` (optional `TiktokenTokenCounter`) | ✅ Production Ready |
| **Summarizer** | `Summarizer` | `ExtractiveSummarizer` & `ResilientSummarizer` (LLM + fallback) | ✅ Production Ready |
| **Vector RAG** | `VectorMemory` | Dense cosine similarity + `HashEmbedder` | ✅ Production Ready |
| **Persistence** | `MemoryStore` | Thread-safe SQLite store (`:memory:` or disk) | ✅ Production Ready |

## 🗺️ Roadmap & Changelog

- 📖 **Architecture Overview**: See [`docs/architecture.md`](docs/architecture.md) for architectural design notes.
- 🎯 **Project Roadmap**: See [`ROADMAP.md`](ROADMAP.md) for planned features (Async support, vector DB integrations, streaming counters).
- 📜 **Changelog**: See [`CHANGELOG.md`](CHANGELOG.md) for version release notes.

## 📁 Repository Layout

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
ROADMAP.md                   # Future milestones & development plans
CHANGELOG.md                 # Version history & release notes
```

## 📦 Installation

```bash
pip install agent-memory
```

Or from a local clone:

```bash
git clone https://github.com/Pierreg99/agent-memory.git
cd agent-memory
pip install -e .
```

## 🧪 Tests

```bash
pip install pytest
python -m pytest tests/ -v
# 48 passed
```

## ⚙️ Configuration

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

## 💻 Demo

```bash
PYTHONPATH=. python examples/run_demo.py
```

## 📄 License

MIT — see `LICENSE`.

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

## Demo

```bash
PYTHONPATH=. python examples/run_demo.py
```

## Roadmap & Progress Plan

### Completed (v0.1.0)
- [x] **Core Orchestration**: Single entry point `AgentMemory` with `add_user`, `add_assistant`, `add_system`, `add_long_term`, and `prepare`.
- [x] **Context Windowing**: Token-budget aware sliding, truncate-oldest, and summarize-old strategies.
- [x] **Summarization Engine**: Zero-dependency extractive summarizer with keyword scoring + fallback-resilient LLM summarizer adapter.
- [x] **Vector RAG Memory**: In-process cosine retrieval using deterministic feature hash embeddings or `sentence-transformers`.
- [x] **Persistence Layer**: Thread-safe SQLite store with schema auto-initialization for ephemeral or file-backed usage.
- [x] **Config & Reliability**: Deep-merge YAML configuration and 100% passing test suite (48 unit/integration tests).

### Near-Term (v0.2.0)
- [ ] **Async API Support**: First-class `async` methods (`aadd_user`, `aprepare`) for high-concurrency agent event loops.
- [ ] **External Vector Store Adapters**: Pluggable integrations for FAISS, Qdrant, and Chroma vector backends.
- [ ] **Hybrid Search**: Hybrid lexical (BM25) + dense vector recall for long-term facts.
- [ ] **Expanded LLM Providers**: Dedicated summarization adapters for Anthropic Claude, Ollama, and local vLLM instances.

### Long-Term (v1.0.0)
- [ ] **Graph & Entity Memory**: Structured entity extraction and relationship tracking across multi-turn sessions.
- [ ] **Memory Consolidation & Decay**: Automated periodic memory pruning, dynamic importance re-ranking, and fact deduplication.
- [ ] **Multi-Agent Shared Memory**: Multi-tenant memory partitions with fine-grained access policies for multi-agent teams.
- [ ] **Memory Inspection CLI**: Visual interactive inspector tool for session history, vector spaces, and summary provenance.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release history and version details.

## License

MIT — see `LICENSE`.

# Memory Lifecycle

`agent-memory` now has an explicit lifecycle for durable semantic memory.

## Durable vectors

When `vector.persist_embeddings` is enabled, long-term memories and generated
summaries are stored with their normalized embeddings in SQLite. Constructing a
new `AgentMemory` against the same database restores the in-process vector index.
If an embedding dimension no longer matches the configured backend, the entry is
re-embedded from its stored content.

## Deletion

```python
mem.clear_session("user-123")
```

This removes conversation messages, summaries, long-term facts, and persisted
vectors for that session only.

## Export

```python
payload = mem.export_session("user-123")
```

The result contains JSON-serializable message, long-term, vector, and latest
summary data. Applications are responsible for securing exported files.

## Retention

```yaml
retention:
  enabled: true
  days: 30
  run_on_start: true
```

Or trigger the purge explicitly:

```python
counts = mem.purge_expired()
```

The purge is timestamp-based and covers every persisted memory layer.

## Prompt-budget guarantee

`prepare()` performs a final fit after retrieval and summarization. Retrieval
items are trimmed first, then oldest recent turns, then oversized summaries,
and finally an oversized system prompt. The reported `MemoryPack.used_tokens`
is capped at the configured prompt-side budget.

For critical model-specific token accounting, configure `tokens.backend:
tiktoken` with the appropriate encoding.

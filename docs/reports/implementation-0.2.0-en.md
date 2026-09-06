# Agent Memory 0.2.0 — Implementation Report

## Scope

The previously identified P0/P1 findings have been implemented in the 0.2.0 revision.

## Implemented

### Durable semantic memory

Long-term memories and generated summaries can be stored in SQLite together with
their embeddings. On process restart, the in-memory vector index is rebuilt from
the database. If a persisted vector has an incompatible dimension, it is
re-embedded from the stored content.

### Summary lifecycle

`source_message_ids` now act as a coverage signal. Message IDs already covered
by the latest summary are excluded from later summary cycles, preventing repeat
compression of the same history. Summary records remain persisted and traceable.

### Prompt safety

Windowing never uses `keep_last_turns` to break the hard prompt-side budget.
After retrieval and summarization, the fully rendered `MemoryPack` is budgeted
again. Retrieval items, oldest recent turns, oversized summaries, and finally
pathological system prompts can be trimmed to preserve the configured ceiling.

### Privacy/lifecycle

New lifecycle APIs include `clear_session()`, `export_session()`, and
`purge_expired()`. Retention purging covers messages, summaries, long-term
facts, and persisted vectors.

### Quality hardening

Core Pydantic models validate important boundaries. Extractive summarization
handles Unicode and German sentence structure more reliably. `VectorMemory`
is thread-safe, supports upserts, and can rebuild stale vectors.

## Tests and CI

Regression tests cover restart rehydration, session deletion, retention,
prompt-budget invariants, summary coverage, model validation, and Unicode.
A reproducible local benchmark and CI smoke checks for compilation and benchmark
execution were added.

## Remaining limitations

The built-in vector index remains O(N). Large deployments should replace it
with a persistent ANN/hybrid backend. Semantic retrieval and summarization
quality should be evaluated against fixed task datasets using metrics such as
Recall@K and MRR. Hosted multi-tenant systems still require authentication,
authorization, encryption at rest, audit logging, and provider-specific data
governance.

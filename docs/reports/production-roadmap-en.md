# Production Roadmap — Agent Memory

## Goal

This roadmap turns the repository analysis into concrete, prioritized work for reliable production use.

## P0 — fix first

### 1. Persistent vector index
`VectorMemory` currently keeps entries and embeddings only in Python lists. SQLite persists messages, summaries, and long-term facts, but not embeddings. After a process restart, semantic retrieval therefore starts empty.

**Action:** define a persistable embedding/index abstraction and implement at least one SQLite-backed persistence mode. For larger deployments, add adapters for Qdrant, pgvector, or FAISS with persisted index metadata.

### 2. Consistent summary chains
`prepare()` can generate a new summary when the threshold is exceeded, while previous summary rows remain. The data model should explicitly represent which message range a summary covers and which summary revision is current.

**Action:** introduce monotonic summary coverage, versioning, and idempotency checks.

### 3. Hard token-budget invariant
The default tokenizer is heuristic. Production usage needs model-aware accounting and a preflight guarantee that the final chat payload stays inside the configured budget.

**Action:** configure a `model_name`/tokenizer profile, add preflight validation, and clearly mark approximate token counts when an exact tokenizer is unavailable.

### 4. Memory lifecycle and deletion
A production memory layer needs explicit retention, correction, deletion, and export semantics. `clear_session()` exists, but retention and garbage-collection policies are missing.

**Action:** add TTL/retention, `forget(entry_id)`, metadata-based deletion, export/import, and verifiable deletion workflows.

## P1 — next

### Retrieval quality
The current vector store performs linear search across all in-memory vectors. This is fine for small collections but does not scale well.

**Actions:** hybrid lexical + semantic retrieval, recency/importance weighting, duplicate suppression, diversity controls, and optional reranking.

### Multilingual summaries
The extractive summarizer uses a small English stopword list and English-oriented sentence segmentation. Quality is therefore limited for German and other languages.

**Actions:** language profiles or language-agnostic provider strategy; German/English regression tests; structured LLM summarization.

### Observability
Track token-budget usage, summary triggers, retrieval hit rate, latency, errors/fallbacks, and memory growth.

**Action:** add a provider-neutral telemetry/callback interface.

### Concurrency
Thread-local SQLite connections are present, but highly concurrent server usage lacks explicit transaction and pooling guidance.

**Actions:** document connection lifecycle, make WAL optional, add busy timeout/retry handling, and support transactional batch operations.

## P2 — maturity

- Versioned storage schema and migrations
- Multi-tenant namespace isolation
- Application-level encryption for sensitive memory data
- Secrets/PII redaction hooks
- Memory provenance and source attribution
- Evaluation suite against realistic conversations
- Benchmarks for N=1k/10k/100k entries
- Stable semantic-versioning policy

## Recommended target architecture

```text
AgentMemory
  |
  +-- Context Policy
  |     +-- Tokenizer
  |     +-- Windowing
  |     +-- Summary policy
  |
  +-- Memory Service
  |     +-- Working memory
  |     +-- Long-term memory
  |     +-- Retrieval / reranking
  |     +-- Provenance
  |
  +-- Storage Adapters
  |     +-- SQLite
  |     +-- pgvector/Qdrant/etc.
  |
  +-- Governance
        +-- retention
        +-- deletion
        +-- PII controls
        +-- audit/telemetry
```

## Production acceptance criteria

1. Restarting the process does not unexpectedly change retrieval behavior.
2. No generated prompt exceeds its configured token budget.
3. Every summary is traceable and idempotent.
4. Individual sessions/tenants can be fully deleted.
5. Retrieval quality can be evaluated reproducibly.
6. Optional LLM and embedding backend failures degrade in a controlled way.

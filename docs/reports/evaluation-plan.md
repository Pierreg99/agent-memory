# Agent Memory Evaluation Plan

## Purpose

Provide a reproducible evaluation layer for memory quality, context efficiency, persistence correctness, and operational behavior.

## Metrics

### Retrieval
- Recall@k
- Precision@k
- MRR
- nDCG@k
- session-isolation error rate
- duplicate retrieval rate

### Summarization
- factual consistency
- decision preservation
- entity/number preservation
- omission rate
- summary token compression ratio
- summary latency and fallback rate

### Context management
- budget violation rate
- average utilization
- recent-turn retention rate
- pinned-system retention rate

### Storage
- restart recovery success rate
- deletion verification rate
- concurrent write error rate
- query latency p50/p95/p99

## Required test datasets

1. English multi-turn conversations
2. German multi-turn conversations
3. Mixed-language conversations
4. Long-context conversations with repeated facts
5. Conflicting facts requiring recency/importance handling
6. Multiple sessions with overlapping vocabulary
7. PII-containing synthetic conversations for governance tests

## Experiment matrix

| Dimension | Variants |
|---|---|
| Tokenizer | heuristic / tiktoken |
| Summarizer | extractive / LLM |
| Embedder | hash / sentence-transformers |
| Retrieval | lexical / semantic / hybrid |
| Scale | 100 / 1k / 10k / 100k entries |
| Language | EN / DE / mixed |

## Gates

A release should fail evaluation when any of these occur:

- token budget violation > 0
- cross-session retrieval > 0
- unrecoverable persisted-memory loss > 0
- deletion verification failure > 0
- regression beyond an agreed retrieval/summarization threshold

## Benchmark harness design

Keep benchmark inputs deterministic and versioned. Store expected relevant entry IDs independently of implementation. Record configuration, library version, Python version, model/provider identifier, and random seeds.

## Recommended CI tiers

**PR:** unit tests, isolation tests, budget invariants, small retrieval benchmark.

**Nightly:** multilingual summarization, larger retrieval benchmark, restart/recovery tests.

**Release:** full matrix, persistence migration tests, performance benchmark, governance tests.

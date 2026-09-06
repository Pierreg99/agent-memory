# Evaluation

The repository evaluates memory quality in four layers.

## 1. Functional correctness

Run the complete test suite:

```bash
python -m pytest tests/ -v
```

Core invariants include session isolation, durable vector rehydration, summary
coverage monotonicity, strict prompt budgets, lifecycle deletion, retention,
Unicode/German extraction, and Pydantic boundary validation.

## 2. Retrieval quality

Measure Recall@K and MRR on a fixed set of synthetic facts with known query-to-
fact relevance. Keep datasets deterministic so changes to the embedder or
ranking policy can be compared across revisions.

Recommended matrix:

| Backend | K | Dataset size |
|---------|---:|---:|
| hash | 1, 4, 8 | 100 / 1,000 / 10,000 |
| sentence-transformers | 1, 4, 8 | 100 / 1,000 / 10,000 |

## 3. Context compression quality

Track:

- source-message coverage,
- summary token count,
- repeated-summary rate,
- key decision retention,
- final prompt token utilization.

The `summarize_old` lifecycle should not re-process message IDs already covered
by the latest summary.

## 4. Performance

Run:

```bash
PYTHONPATH=. python benchmarks/run_memory_bench.py
```

The benchmark reports corpus size, vector count, median query latency, and
maximum observed query latency for the local O(N) index.

### Release gates

A release should keep all functional tests green, preserve session isolation,
keep the final prompt within the configured budget, and document any retrieval
or latency regression before publishing.

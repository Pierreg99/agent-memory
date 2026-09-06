"""Small dependency-light benchmark suite for local regression checks.

Usage:
    PYTHONPATH=. python benchmarks/run_memory_bench.py
"""
from __future__ import annotations

import statistics
import time

from agent_memory import AgentMemory
from agent_memory.config.settings import MemorySettings


def build_memory(n: int = 1000) -> AgentMemory:
    settings = MemorySettings.from_dict({
        "window": {"max_tokens": 4000, "reserve_for_response": 500},
        "vector": {"enabled": True, "backend": "hash", "dim": 128, "top_k": 8},
        "persistence": {"enabled": True, "sqlite_path": ":memory:", "auto_commit": True},
    })
    mem = AgentMemory(settings)
    for i in range(n):
        mem.add_long_term(
            f"Fact {i}: project tag={i % 17}; the system processes durable agent memory.",
            importance=(i % 10) / 10,
            metadata={"tag": i % 17},
        )
    return mem


def benchmark_query(mem: AgentMemory, rounds: int = 20) -> tuple[float, float]:
    samples = []
    for _ in range(rounds):
        started = time.perf_counter()
        mem.prepare("durable agent memory project", system_prompt="You are a benchmark agent.")
        samples.append((time.perf_counter() - started) * 1000)
    return statistics.median(samples), max(samples)


def main() -> None:
    mem = build_memory()
    median_ms, max_ms = benchmark_query(mem)
    print(f"entries={mem.stats()['long_term_count']}")
    print(f"vector_count={mem.stats()['vector_count']}")
    print(f"query_median_ms={median_ms:.3f}")
    print(f"query_max_ms={max_ms:.3f}")
    mem.close()


if __name__ == "__main__":
    main()

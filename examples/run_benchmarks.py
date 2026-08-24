"""Comprehensive Quality, Performance, and Quality-Net-Worth Benchmark Suite for `agent-memory`.

Evaluates:
1. Token Counter performance and accuracy.
2. Context Windowing compliance and latency.
3. RAG Vector Memory recall, precision, and search throughput.
4. SQLite Persistence read/write throughput and latency.
5. Extractive Summarization retention quality.
6. End-to-end Orchestrator context preparation overhead.
"""
from __future__ import annotations

import json
import time
import os
import resource
import numpy as np
from typing import Any, Dict, List

from agent_memory import AgentMemory
from agent_memory.config.settings import MemorySettings, VectorConfig, SummaryConfig, WindowConfig, TokenConfig
from agent_memory.core.models import Message, MemoryEntry, MemoryQuery
from agent_memory.core.types import Role, WindowStrategy, MemoryKind
from agent_memory.window.token_counter import HeuristicTokenCounter, build_counter
from agent_memory.window.window_manager import WindowManager
from agent_memory.vector.memory import VectorMemory
from agent_memory.vector.embeddings import HashEmbedder
from agent_memory.summary.summarizer import ExtractiveSummarizer
from agent_memory.persistence.store import MemoryStore


def benchmark_token_counters() -> Dict[str, Any]:
    print("--- Running Token Counter Benchmarks ---")
    sample_texts = [
        "Short text sentence.",
        "A medium length paragraph with multiple words, symbols like $100, and standard conversation flow." * 5,
        "Long technical text context windowing evaluation. " * 200
    ]

    counters = {
        "heuristic": HeuristicTokenCounter(),
        "heuristic_custom_ratio": HeuristicTokenCounter(TokenConfig(chars_per_token=3.5)),
    }

    results = {}
    for name, counter in counters.items():
        start = time.perf_counter()
        iterations = 500
        total_tokens = 0
        for _ in range(iterations):
            for t in sample_texts:
                total_tokens += counter.count_text(t)
        elapsed = time.perf_counter() - start
        ops_sec = (iterations * len(sample_texts)) / elapsed
        results[name] = {
            "elapsed_sec": round(elapsed, 5),
            "ops_per_sec": round(ops_sec, 2),
            "total_tokens_counted": total_tokens
        }
    return results


def benchmark_window_manager() -> Dict[str, Any]:
    print("--- Running Window Manager Benchmarks ---")
    counter = HeuristicTokenCounter()
    messages = [
        Message(role=Role.USER if i % 2 == 0 else Role.ASSISTANT, content=f"Message {i}: " + ("word " * (i % 20 + 5)))
        for i in range(200)
    ]

    results = {}
    for strategy in [WindowStrategy.SLIDING, WindowStrategy.TRUNCATE_OLDEST]:
        cfg = WindowConfig(max_tokens=1500, reserve_for_response=500, keep_last_turns=4, strategy=strategy)
        wm = WindowManager(cfg, counter)

        start = time.perf_counter()
        iterations = 100
        budget_violations = 0
        for _ in range(iterations):
            res = wm.apply(messages, system_prompt="You are a helpful assistant.")
            if res.used_tokens > res.budget_tokens:
                budget_violations += 1
        elapsed = time.perf_counter() - start

        results[strategy.value] = {
            "elapsed_sec": round(elapsed, 5),
            "ops_per_sec": round(iterations / elapsed, 2),
            "budget_violations": budget_violations,
            "kept_count": len(res.kept),
            "used_tokens": res.used_tokens,
            "budget_tokens": res.budget_tokens
        }
    return results


def benchmark_vector_memory() -> Dict[str, Any]:
    print("--- Running Vector Memory Recall & Latency Benchmarks ---")
    cfg = VectorConfig(dim=64, top_k=5, min_similarity=0.0)
    vec_mem = VectorMemory(cfg)

    # Ingest facts
    facts = [
        "Alice loves hiking in Colorado mountains.",
        "Bob prefers swimming in the Atlantic ocean.",
        "Charlie works as a senior software developer in Seattle.",
        "Alice's favorite food is Italian pasta.",
        "David enjoys reading science fiction novels.",
        "The project deadline is scheduled for October 15th.",
        "Database connection parameter timeout is set to 30 seconds.",
        "Alice plays violin on weekends.",
        "Charlie's favorite programming language is Python.",
        "Eve is an expert in quantum computing algorithms."
    ]

    start_ingest = time.perf_counter()
    entries = []
    for f in facts:
        e = MemoryEntry(session_id="s1", kind=MemoryKind.LONG_TERM, content=f)
        vec_mem.add(e)
        entries.append(e)
    ingest_time = time.perf_counter() - start_ingest

    # Measure query performance & recall accuracy
    queries = [
        ("What does Alice like doing outdoor?", ["hiking", "Colorado"]),
        ("Where does Charlie work and what is his job?", ["software", "developer"]),
        ("When is the project deadline?", ["October 15th"]),
    ]

    start_query = time.perf_counter()
    iterations = 200
    total_retrieved = 0
    hit_count = 0
    total_relevant = 0

    for iter_i in range(iterations):
        for q_str, keywords in queries:
            q = MemoryQuery(session_id="s1", query_text=q_str, top_k=3)
            retrieved = vec_mem.query(q)
            if iter_i == 0:
                total_retrieved += len(retrieved)
                # Check keyword match recall
                for r in retrieved:
                    if any(kw.lower() in r.content.lower() for kw in keywords):
                        hit_count += 1
                        break
                total_relevant += 1

    query_time = time.perf_counter() - start_query
    recall_rate = hit_count / total_relevant if total_relevant > 0 else 0.0

    return {
        "fact_count": len(facts),
        "ingest_time_sec": round(ingest_time, 5),
        "ingest_per_fact_sec": round(ingest_time / len(facts), 6),
        "query_ops_per_sec": round((iterations * len(queries)) / query_time, 2),
        "recall_top3_rate": round(recall_rate, 4),
    }


def benchmark_persistence() -> Dict[str, Any]:
    print("--- Running SQLite Persistence Benchmarks ---")
    db_path = ":memory:"
    store = MemoryStore(path=db_path, auto_commit=True)

    # Batch write messages
    messages = [
        Message(role=Role.USER if i % 2 == 0 else Role.ASSISTANT, content=f"Message content number {i}")
        for i in range(500)
    ]

    start_write = time.perf_counter()
    store.add_messages("s1", messages)
    write_time = time.perf_counter() - start_write

    # Read messages
    start_read = time.perf_counter()
    iterations = 100
    for _ in range(iterations):
        read_msgs = store.get_messages("s1")
    read_time = time.perf_counter() - start_read

    return {
        "written_messages": len(messages),
        "write_time_sec": round(write_time, 5),
        "write_msgs_per_sec": round(len(messages) / write_time, 2),
        "read_iterations": iterations,
        "read_ops_per_sec": round(iterations / read_time, 2),
        "read_returned_count": len(read_msgs)
    }


def benchmark_extractive_summarizer() -> Dict[str, Any]:
    print("--- Running Summarizer Retention Quality Benchmarks ---")
    summarizer = ExtractiveSummarizer()
    messages = [
        Message(role=Role.USER, content="Our team meeting is scheduled at 10 AM on Monday."),
        Message(role=Role.ASSISTANT, content="Got it. I will prepare the quarterly performance report for the meeting."),
        Message(role=Role.USER, content="Make sure to include revenue growth metrics and user retention statistics."),
        Message(role=Role.ASSISTANT, content="Understood. Revenue growth and user retention stats will be highlighted in slide 3."),
    ]

    start = time.perf_counter()
    summary, covered_ids = summarizer.summarize_messages(messages, max_tokens=30)
    elapsed = time.perf_counter() - start

    # Keywords that should ideally be preserved
    important_keywords = ["meeting", "10 AM", "Monday", "revenue", "retention"]
    retained_keywords = [kw for kw in important_keywords if kw.lower() in summary.lower()]
    retention_ratio = len(retained_keywords) / len(important_keywords)

    return {
        "summary_output": summary,
        "covered_messages_count": len(covered_ids),
        "execution_time_sec": round(elapsed, 5),
        "important_keywords": important_keywords,
        "retained_keywords": retained_keywords,
        "retention_score": round(retention_ratio, 4)
    }


def benchmark_orchestrator() -> Dict[str, Any]:
    print("--- Running AgentMemory Orchestrator & Agentic Routines Benchmarks ---")
    mem = AgentMemory.from_config({
        "persistence": {"sqlite_path": ":memory:"},
        "vector": {"enabled": True},
        "window": {"max_tokens": 1000}
    })

    # Ingest conversation & long-term facts
    start_ingest = time.perf_counter()
    for i in range(50):
        mem.add_user(f"User turn {i}: requesting analysis on component {i}")
        mem.add_assistant(f"Assistant turn {i}: response for component {i}")

    mem.add_long_term("System requirement: All API endpoints must return within 200ms.")
    mem.add_long_term("System architecture: Database layer uses SQLite in-memory mode.")
    ingest_elapsed = time.perf_counter() - start_ingest

    # Test chat turn routine
    start_routine = time.perf_counter()
    mem.chat_turn("Routine query test", assistant_responder=lambda pack: "Routine response")
    routine_elapsed = time.perf_counter() - start_routine

    # Test consolidation routine
    start_consolidation = time.perf_counter()
    mem.consolidate_session()
    consolidation_elapsed = time.perf_counter() - start_consolidation

    # Test maintenance routine
    start_maint = time.perf_counter()
    maint_stats = mem.maintain_memory(decay_factor=0.9, min_importance=0.1)
    maint_elapsed = time.perf_counter() - start_maint

    # Prepare LLM context
    start_prep = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        pack = mem.prepare("What are the system performance requirements?", system_prompt="You are an helpful AI engineer.")
    prep_elapsed = time.perf_counter() - start_prep

    return {
        "total_messages": mem.stats()["message_count"],
        "total_long_term_facts": mem.stats()["long_term_count"],
        "ingest_time_sec": round(ingest_elapsed, 5),
        "chat_turn_routine_sec": round(routine_elapsed, 5),
        "consolidation_routine_sec": round(consolidation_elapsed, 5),
        "maintenance_routine_sec": round(maint_elapsed, 5),
        "prepare_ops_per_sec": round(iterations / prep_elapsed, 2),
        "prepared_pack_messages": len(pack.to_chat_messages()),
        "prepared_used_tokens": pack.used_tokens,
        "prepared_retrieved_facts_count": len(pack.retrieved_facts)
    }


def run_all_benchmarks() -> Dict[str, Any]:
    mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

    results = {
        "token_counter": benchmark_token_counters(),
        "window_manager": benchmark_window_manager(),
        "vector_memory": benchmark_vector_memory(),
        "persistence": benchmark_persistence(),
        "summarizer": benchmark_extractive_summarizer(),
        "orchestrator": benchmark_orchestrator(),
    }

    mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    results["system_memory"] = {
        "maxrss_before_mb": round(mem_before, 2),
        "maxrss_after_mb": round(mem_after, 2),
        "maxrss_delta_mb": round(mem_after - mem_before, 2),
    }
    return results


if __name__ == "__main__":
    report = run_all_benchmarks()
    print("\n================ BENCHMARK RESULTS SUMMARY ================")
    print(json.dumps(report, indent=2))

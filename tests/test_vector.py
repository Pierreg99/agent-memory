"""Tests for vector memory and embeddings."""
from agent_memory.config.settings import VectorConfig
from agent_memory.core.models import MemoryEntry, MemoryQuery
from agent_memory.core.types import MemoryKind, Role
from agent_memory.vector.embeddings import HashEmbedder
from agent_memory.vector.memory import VectorMemory


def test_hash_embedder_is_deterministic():
    cfg = VectorConfig(dim=64)
    e = HashEmbedder(cfg)
    v1 = e.embed_text("the quick brown fox")
    v2 = e.embed_text("the quick brown fox")
    assert v1 == v2
    assert len(v1) == 64


def test_hash_embedder_normalized():
    import math

    e = HashEmbedder(VectorConfig(dim=32))
    v = e.embed_text("hello world")
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-6


def test_hash_embedder_similar_texts_have_high_similarity():
    e = HashEmbedder(VectorConfig(dim=128))
    a = e.embed_text("I love hiking in the Alps")
    b = e.embed_text("I love hiking in the Alps")
    # Identical texts => dot product = 1.0
    dot = sum(x * y for x, y in zip(a, b))
    assert dot > 0.99


def test_vector_memory_add_and_query():
    cfg = VectorConfig(dim=64, top_k=2, min_similarity=0.0)
    vm = VectorMemory(cfg)
    e1 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User's favorite color is blue",
    )
    e2 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User dislikes spicy food",
    )
    e3 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User enjoys painting landscapes",
    )
    vm.add(e1)
    vm.add(e2)
    vm.add(e3)

    q = MemoryQuery(session_id="s1", query_text="color", top_k=2)
    results = vm.query(q)
    assert len(results) == 2
    # The color fact should rank first (lexical overlap)
    assert "color" in results[0].content.lower()


def test_vector_memory_filters_by_kind():
    cfg = VectorConfig(dim=32, top_k=10)
    vm = VectorMemory(cfg)
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="Fact about apples",
        )
    )
    vm.add(
        MemoryEntry(
            kind=MemoryKind.SUMMARY,
            session_id="s1",
            content="Earlier we discussed apples",
        )
    )
    q = MemoryQuery(
        session_id="s1",
        query_text="apples",
        kinds=[MemoryKind.LONG_TERM],
    )
    results = vm.query(q)
    assert len(results) == 1
    assert results[0].kind == MemoryKind.LONG_TERM


def test_vector_memory_filters_by_importance():
    cfg = VectorConfig(dim=32, top_k=10)
    vm = VectorMemory(cfg)
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="trivial apples fact",
            importance=0.1,
        )
    )
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="critical apples fact",
            importance=0.9,
        )
    )
    q = MemoryQuery(session_id="s1", query_text="apples", min_importance=0.5)
    results = vm.query(q)
    assert len(results) == 1
    assert "critical" in results[0].content


def test_vector_memory_clear():
    cfg = VectorConfig(dim=16)
    vm = VectorMemory(cfg)
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="something",
        )
    )
    assert len(vm) == 1
    vm.clear()
    assert len(vm) == 0

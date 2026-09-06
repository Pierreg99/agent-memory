"""Gap-filling tests: session isolation, config env, errors, helpers."""
from __future__ import annotations

import pytest

from agent_memory import AgentMemory
from agent_memory.config.settings import (
    MemorySettings,
    SummaryConfig,
    VectorConfig,
    load_settings,
)
from agent_memory.core.models import MemoryEntry, MemoryQuery
from agent_memory.core.types import MemoryKind, Role
from agent_memory.persistence.store import MemoryStore
from agent_memory.summary.summarizer import (
    ExtractiveSummarizer,
    LLMSummarizer,
    ResilientSummarizer,
)
from agent_memory.vector.memory import VectorMemory


def test_vector_query_filters_by_session_id():
    vm = VectorMemory(VectorConfig(dim=32, top_k=10))
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="Alice likes tea",
        )
    )
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s2",
            content="Bob likes coffee",
        )
    )
    results = vm.query(
        MemoryQuery(session_id="s1", query_text="likes tea coffee", top_k=10)
    )
    assert len(results) == 1
    assert results[0].session_id == "s1"
    assert "Alice" in results[0].content


def test_vector_clear_session_preserves_other_sessions():
    vm = VectorMemory(VectorConfig(dim=32))
    vm.add(
        MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s1", content="alpha")
    )
    vm.add(
        MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s2", content="beta")
    )
    vm.clear_session("s1")
    assert len(vm) == 1
    assert vm._entries[0].session_id == "s2"


def test_orchestrator_clear_session_only_clears_that_session_vector():
    mem = AgentMemory.from_config(
        {
            "vector": {"enabled": True, "dim": 32, "top_k": 3},
            "persistence": {"sqlite_path": ":memory:"},
        }
    )
    mem.add_long_term("fact for default", session_id="default")
    mem.add_long_term("fact for other", session_id="other")
    assert mem.stats("default")["vector_count"] == 2  # shared store length
    mem.clear_session("default")
    assert mem.stats("default")["message_count"] == 0
    assert mem.stats("default")["long_term_count"] == 0
    # Vector should still hold the other session's fact
    assert len(mem.vector) == 1
    assert mem.vector._entries[0].session_id == "other"


def test_vector_metadata_filter():
    vm = VectorMemory(VectorConfig(dim=32, top_k=10))
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="tagged fact about cats",
            metadata={"source": "profile"},
        )
    )
    vm.add(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id="s1",
            content="untagged fact about cats",
            metadata={"source": "chat"},
        )
    )
    q = MemoryQuery(
        session_id="s1",
        query_text="cats",
        metadata_filter={"source": "profile"},
    )
    results = vm.query(q)
    assert len(results) == 1
    assert results[0].metadata["source"] == "profile"


def test_add_many_long_term():
    mem = AgentMemory.from_config(
        {"vector": {"dim": 16}, "persistence": {"sqlite_path": ":memory:"}}
    )
    entries = mem.add_many_long_term(["one", "two", "three"], importance=0.5)
    assert len(entries) == 3
    assert mem.stats()["long_term_count"] == 3
    assert all(e.importance == 0.5 for e in entries)


def test_add_rejects_empty_content():
    mem = AgentMemory.from_config({"persistence": {"sqlite_path": ":memory:"}})
    with pytest.raises(ValueError, match="non-empty"):
        mem.add_user("   ")


def test_add_rejects_invalid_role():
    mem = AgentMemory.from_config({"persistence": {"sqlite_path": ":memory:"}})
    with pytest.raises(ValueError, match="invalid role"):
        mem.add("narrator", "hello")


def test_invalid_window_strategy_raises():
    with pytest.raises(ValueError, match="window.strategy"):
        load_settings({"window": {"strategy": "teleport"}})


def test_memory_config_path_env(tmp_path, monkeypatch):
    cfg = tmp_path / "override.yaml"
    cfg.write_text("window:\n  max_tokens: 1234\n", encoding="utf-8")
    monkeypatch.setenv("MEMORY_CONFIG_PATH", str(cfg))
    s = load_settings()
    assert s.window.max_tokens == 1234
    # overrides still win
    s2 = load_settings({"window": {"max_tokens": 999}})
    assert s2.window.max_tokens == 999


def test_memory_config_path_missing(monkeypatch):
    monkeypatch.setenv("MEMORY_CONFIG_PATH", "/no/such/config.yaml")
    with pytest.raises(FileNotFoundError, match="MEMORY_CONFIG_PATH"):
        load_settings()


def test_from_yaml_and_missing(tmp_path):
    cfg = tmp_path / "mem.yaml"
    cfg.write_text(
        "window:\n  max_tokens: 2048\n  strategy: truncate_oldest\n",
        encoding="utf-8",
    )
    mem = AgentMemory.from_yaml(str(cfg))
    assert mem.settings.window.max_tokens == 2048
    with pytest.raises(FileNotFoundError):
        AgentMemory.from_yaml(str(tmp_path / "missing.yaml"))


def test_file_store_helper(tmp_path):
    path = tmp_path / "nested" / "store.db"
    store = MemoryStore.file_store(path)
    assert path.exists() or path.parent.exists()
    from agent_memory.core.models import Message

    store.add_message("s1", Message(role=Role.USER, content="disk"))
    store.close()
    store2 = MemoryStore(path=str(path))
    assert store2.get_messages("s1")[0].content == "disk"
    store2.close()


def test_llm_summarizer_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = LLMSummarizer(SummaryConfig(backend="llm"))
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        s.summarize_text("hello world. another sentence.", max_tokens=40)


def test_resilient_summarizer_falls_back_to_extractive(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = ResilientSummarizer(SummaryConfig(backend="llm", min_messages_to_summarize=1))
    text = (
        "The expedition climbed the mountain. The weather was clear. "
        "They reached the summit before noon."
    )
    out = s.summarize_text(text, max_tokens=80)
    assert isinstance(out, str)
    assert len(out) > 0
    # Should behave like extractive (no network)
    assert isinstance(s.extractive, ExtractiveSummarizer)


def test_settings_from_yaml_non_mapping(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        MemorySettings.from_yaml(cfg)

"""Tests for the SQLite persistence layer."""
import tempfile
from pathlib import Path

from agent_memory.core.models import MemoryEntry, Message
from agent_memory.core.types import MemoryKind, Role
from agent_memory.persistence.store import MemoryStore


def test_in_memory_store_roundtrip():
    store = MemoryStore(":memory:")
    m = Message(role=Role.USER, content="hi")
    store.add_message("s1", m)
    out = store.get_messages("s1")
    assert len(out) == 1
    assert out[0].content == "hi"
    assert out[0].role == Role.USER


def test_in_memory_store_session_isolation():
    store = MemoryStore(":memory:")
    store.add_message("s1", Message(role=Role.USER, content="for s1"))
    store.add_message("s2", Message(role=Role.USER, content="for s2"))
    assert [m.content for m in store.get_messages("s1")] == ["for s1"]
    assert [m.content for m in store.get_messages("s2")] == ["for s2"]


def test_persistence_to_disk():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "mem.db")
        s1 = MemoryStore(path=path)
        s1.add_message("s1", Message(role=Role.USER, content="persisted"))
        s1.close()
        # Re-open
        s2 = MemoryStore(path=path)
        msgs = s2.get_messages("s1")
        assert len(msgs) == 1
        assert msgs[0].content == "persisted"
        s2.close()


def test_summary_roundtrip():
    store = MemoryStore(":memory:")
    entry = MemoryEntry(
        kind=MemoryKind.SUMMARY,
        session_id="s1",
        role=Role.SUMMARY,
        content="summary content",
        source_message_ids=["m1", "m2"],
    )
    store.add_summary("s1", entry)
    got = store.get_latest_summary("s1")
    assert got is not None
    assert got.content == "summary content"
    assert got.source_message_ids == ["m1", "m2"]


def test_long_term_roundtrip():
    store = MemoryStore(":memory:")
    entry = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User is named Alice",
        importance=0.8,
    )
    store.add_long_term(entry)
    out = store.get_long_term("s1")
    assert len(out) == 1
    assert out[0].content == "User is named Alice"
    assert out[0].importance == 0.8


def test_clear_session():
    store = MemoryStore(":memory:")
    store.add_message("s1", Message(role=Role.USER, content="x"))
    store.add_long_term(
        MemoryEntry(
            kind=MemoryKind.LONG_TERM, session_id="s1", content="fact"
        )
    )
    store.add_summary(
        "s1",
        MemoryEntry(
            kind=MemoryKind.SUMMARY,
            session_id="s1",
            content="sum",
            source_message_ids=[],
        ),
    )
    store.clear_session("s1")
    assert store.get_messages("s1") == []
    assert store.get_latest_summary("s1") is None
    assert store.get_long_term("s1") == []


def test_thread_safety_each_thread_gets_a_connection():
    """A new thread should be able to read what the main thread wrote.

    Note: we use a file-backed store here because in-memory SQLite is
    per-connection. With a file path, all threads see the same data.
    """
    import tempfile
    import threading

    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "thread.db")
        store = MemoryStore(path=path)
        store.add_message("s1", Message(role=Role.USER, content="from main"))

        results = {}

        def worker():
            msgs = store.get_messages("s1")
            results["msgs"] = msgs

        t = threading.Thread(target=worker)
        t.start()
        t.join(timeout=5)
        assert results["msgs"][0].content == "from main"

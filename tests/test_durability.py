"""Regression tests for persistence, restart behavior, and retention."""
import time

from agent_memory import AgentMemory
from agent_memory.config.settings import MemorySettings


def _settings(path: str, **overrides):
    data = {
        "persistence": {"enabled": True, "sqlite_path": path, "auto_commit": True},
        "vector": {"enabled": True, "backend": "hash", "dim": 128, "top_k": 5, "persist_embeddings": True},
        "window": {"max_tokens": 400, "reserve_for_response": 50},
    }
    for key, value in overrides.items():
        data[key] = value
    return MemorySettings.from_dict(data)


def test_vector_rehydrates_after_restart(tmp_path):
    path = str(tmp_path / "memory.db")
    first = AgentMemory(_settings(path))
    first.add_long_term("Alice works on renewable energy research", importance=0.9)
    assert first.stats()["vector_count"] == 1
    first.close()

    second = AgentMemory(_settings(path))
    assert second.stats()["vector_count"] == 1
    pack = second.prepare("renewable energy research")
    assert any("renewable energy" in entry.content for entry in pack.retrieved_facts)
    second.close()


def test_clear_session_removes_durable_vectors(tmp_path):
    path = str(tmp_path / "memory.db")
    mem = AgentMemory(_settings(path))
    mem.add_long_term("session secret", session_id="s1")
    mem.add_long_term("keep this", session_id="s2")
    mem.clear_session("s1")
    mem.close()

    restored = AgentMemory(_settings(path))
    assert all(e.session_id != "s1" for e in restored.store.get_vector_entries())
    assert any(e.session_id == "s2" for e in restored.store.get_vector_entries())
    restored.close()


def test_retention_purges_all_memory_layers(tmp_path):
    path = str(tmp_path / "memory.db")
    settings = _settings(path, retention={"enabled": True, "days": 1})
    mem = AgentMemory(settings)
    old = time.time() - (2 * 86400)
    msg = mem.add_user("old message")
    msg.timestamp = old
    mem.store.add_message("default", msg)
    entry = mem.add_long_term("old fact")
    entry.created_at = old
    mem.store.add_long_term(entry)
    mem.vector.clear()
    entry.embedding = mem.vector.embedder.embed_entry(entry)
    mem.vector.add_embedded(entry)
    mem.store.add_vector_entry(entry)

    counts = mem.purge_expired(now=time.time())
    assert counts["messages"] >= 1
    assert counts["long_term"] >= 1
    assert counts["memory_vectors"] >= 1
    assert mem.stats()["message_count"] == 0
    assert mem.stats()["long_term_count"] == 0
    assert len(mem.store.get_vector_entries()) == 0
    mem.close()

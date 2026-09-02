import pytest
from agent_memory import AgentMemory
from agent_memory.core.types import MemoryKind


def test_sub_agent_cannot_write_long_term():
    primary_mem = AgentMemory.from_config()
    sub_mem = primary_mem.create_sub_agent_memory("researcher_subagent", can_write_long_term=False)

    with pytest.raises(PermissionError) as exc_info:
        sub_mem.add_long_term("Subagent unverified conclusion")
    assert "permission to write long-term memory" in str(exc_info.value)


def test_sub_agent_working_memory_isolation():
    primary_mem = AgentMemory.from_config()
    sub_mem = primary_mem.create_sub_agent_memory("search_worker", can_write_long_term=False)

    # Sub-agent stores working entry
    w_entry = sub_mem.add_working("Intermediate search result: draft finding")
    assert w_entry.kind == MemoryKind.WORKING

    # Verify RAG context preparation does NOT retrieve working entries
    pack = primary_mem.prepare("search result")
    assert not any("draft finding" in f.content for f in pack.retrieved_facts)


def test_primary_agent_promotion():
    primary_mem = AgentMemory.from_config()
    sub_mem = primary_mem.create_sub_agent_memory("worker", can_write_long_term=False)

    # Subagent creates working memory entry
    w_entry = sub_mem.add_working("Verified user preference: Python developer", entity="user", attribute="language")

    # Primary agent inspects working memory and promotes it
    working_entries = primary_mem.get_working_entries()
    assert len(working_entries) == 1
    assert working_entries[0].id == w_entry.id

    promoted = primary_mem.promote_working_to_long_term(w_entry.id)
    assert len(promoted) == 1
    assert promoted[0].kind == MemoryKind.LONG_TERM
    assert promoted[0].content == "Verified user preference: Python developer"

    # Verify now retrieved in RAG query
    pack = primary_mem.prepare("programming language")
    assert any("Python developer" in f.content for f in pack.retrieved_facts)


def test_working_entry_does_not_supersede_long_term():
    primary_mem = AgentMemory.from_config()
    lt_entry = primary_mem.add_long_term("User lives in Munich", entity="user", attribute="location")

    sub_mem = primary_mem.create_sub_agent_memory("worker", can_write_long_term=False)
    # Sub-agent adds working memory with same entity/attribute
    sub_mem.add_working("Maybe user lives in Berlin", entity="user", attribute="location")

    # Verify primary long term entry was NOT superseded
    facts = primary_mem.store.get_long_term(primary_mem.default_session)
    assert len(facts) == 1
    assert facts[0].id == lt_entry.id
    assert not facts[0].is_superseded


def test_session_scoped_vector_eviction():
    mem = AgentMemory.from_config({"vector": {"decay_enabled": True, "half_life_days": 1.0, "min_importance_threshold": 0.5}})
    import time
    old_ts = time.time() - (10 * 86400)

    # Session 1 old entry
    mem.add_long_term("Session 1 old fact", session_id="s1", importance=0.8)
    mem.vector._entries[-1].created_at = old_ts

    # Session 2 old entry
    mem.add_long_term("Session 2 old fact", session_id="s2", importance=0.8)
    mem.vector._entries[-1].created_at = old_ts

    # Evict only session 1
    res = mem.evict_stale(session_id="s1")
    assert res["vector_evicted"] == 1

    # Verify s2 old entry is still in vector memory
    s2_entries = [e for e in mem.vector._entries if e.session_id == "s2"]
    assert len(s2_entries) == 1

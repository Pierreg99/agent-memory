from agent_memory import AgentMemory
from agent_memory.core.models import MemoryEntry, MemoryQuery
from agent_memory.core.types import MemoryKind
from agent_memory.persistence.store import MemoryStore
from agent_memory.vector.memory import VectorMemory
from agent_memory.config.settings import VectorConfig


def test_temporal_superseding_vector():
    vm = VectorMemory(VectorConfig())
    e1 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User lives in Munich",
        entity="user",
        attribute="location",
    )
    vm.add(e1)
    assert len(vm) == 1

    # Query before update
    q = MemoryQuery(session_id="s1", query_text="location")
    res = vm.query(q)
    assert len(res) == 1
    assert res[0].content == "User lives in Munich"

    # Add updated fact
    e2 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User lives in Berlin",
        entity="user",
        attribute="location",
    )
    vm.add(e2)

    # Standard query should exclude superseded fact
    res2 = vm.query(q)
    assert len(res2) == 1
    assert res2[0].content == "User lives in Berlin"

    # Query including superseded facts
    q_all = MemoryQuery(session_id="s1", query_text="location", include_superseded=True)
    res_all = vm.query(q_all)
    assert len(res_all) == 2
    assert e1.is_superseded is True
    assert e1.superseded_by == e2.id


def test_temporal_superseding_store():
    store = MemoryStore()
    e1 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User likes tea",
        entity="user",
        attribute="beverage",
    )
    store.add_long_term(e1)

    facts = store.get_long_term("s1")
    assert len(facts) == 1
    assert facts[0].content == "User likes tea"

    e2 = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="User likes coffee",
        entity="user",
        attribute="beverage",
    )
    store.add_long_term(e2)

    # Default get_long_term hides superseded
    facts_active = store.get_long_term("s1")
    assert len(facts_active) == 1
    assert facts_active[0].content == "User likes coffee"

    # Get including superseded
    facts_all = store.get_long_term("s1", include_superseded=True)
    assert len(facts_all) == 2
    superseded = [f for f in facts_all if f.is_superseded]
    assert len(superseded) == 1
    assert superseded[0].content == "User likes tea"


def test_agent_memory_temporal_integration():
    mem = AgentMemory.from_config()
    mem.add_long_term("User lives in Munich", entity="user", attribute="location")
    pack1 = mem.prepare("Where do I live?")
    assert any("Munich" in f.content for f in pack1.retrieved_facts)

    mem.add_long_term("User moved to Berlin", entity="user", attribute="location")
    pack2 = mem.prepare("Where do I live?")
    assert any("Berlin" in f.content for f in pack2.retrieved_facts)
    assert not any("Munich" in f.content for f in pack2.retrieved_facts)

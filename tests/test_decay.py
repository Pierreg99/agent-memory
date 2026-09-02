import time
from agent_memory import AgentMemory
from agent_memory.core.models import MemoryEntry
from agent_memory.core.types import MemoryKind
from agent_memory.vector.memory import VectorMemory
from agent_memory.config.settings import VectorConfig


def test_decay_computation():
    cfg = VectorConfig(decay_enabled=True, half_life_days=10.0)
    vm = VectorMemory(cfg)

    now = time.time()
    # Fact created 10 days ago (1 half life -> importance reduced by 50%)
    ten_days_ago = now - (10 * 86400)
    e = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="Old fact",
        importance=1.0,
        created_at=ten_days_ago,
    )
    vm.add(e)

    eff = vm.compute_effective_importance(e, current_time=now)
    assert abs(eff - 0.5) < 1e-4


def test_eviction_threshold():
    cfg = VectorConfig(decay_enabled=True, half_life_days=5.0, min_importance_threshold=0.2)
    vm = VectorMemory(cfg)

    now = time.time()
    e_recent = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="Recent fact",
        importance=0.5,
        created_at=now - 86400, # 1 day old
    )
    e_old = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id="s1",
        content="Very old fact",
        importance=0.5,
        created_at=now - (20 * 86400), # 20 days old = 4 half-lives -> 0.5 * 0.0625 = 0.03125 < 0.2
    )
    vm.add(e_recent)
    vm.add(e_old)

    evicted = vm.evict(current_time=now)
    assert evicted == 1
    assert len(vm) == 1
    assert vm._entries[0].content == "Recent fact"


def test_eviction_max_entries():
    cfg = VectorConfig(decay_enabled=False, max_entries=2)
    vm = VectorMemory(cfg)

    e1 = MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s1", content="Fact 1", importance=0.3)
    e2 = MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s1", content="Fact 2", importance=0.9)
    e3 = MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s1", content="Fact 3", importance=0.7)

    vm.add(e1)
    vm.add(e2)
    vm.add(e3)

    evicted = vm.evict(min_importance=0.0)
    assert evicted == 1
    assert len(vm) == 2
    contents = [e.content for e in vm._entries]
    assert "Fact 2" in contents
    assert "Fact 3" in contents
    assert "Fact 1" not in contents


def test_orchestrator_evict_stale():
    mem = AgentMemory.from_config({
        "vector": {
            "decay_enabled": True,
            "half_life_days": 10.0,
            "min_importance_threshold": 0.2,
        }
    })
    now = time.time()

    mem.add_long_term("Recent interest", importance=1.0)
    # Add an old item to store manually with old timestamp
    old_entry = MemoryEntry(
        kind=MemoryKind.LONG_TERM,
        session_id=mem.default_session,
        content="Ancient interest",
        importance=0.3,
        created_at=now - (100 * 86400),
    )
    mem.store.add_long_term(old_entry)
    if mem.vector is not None:
        mem.vector.add(old_entry)

    res = mem.evict_stale(current_time=now)
    assert res["vector_evicted"] == 1
    assert res["store_evicted"] == 1

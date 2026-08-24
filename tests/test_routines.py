"""Tests for agentic routines and performance optimizations."""
import pytest
from agent_memory import AgentMemory
from agent_memory.core.models import MemoryEntry, MemoryPack
from agent_memory.core.types import MemoryKind


def test_consolidate_session():
    mem = AgentMemory.from_config({"persistence": {"sqlite_path": ":memory:"}})
    mem.add_user("My favorite food is sushi.")
    mem.add_assistant("I will remember that you love sushi.")
    mem.add_user("Also I am planning a trip to Kyoto next month.")
    mem.add_assistant("Kyoto is wonderful in autumn.")

    summary_entry = mem.consolidate_session()
    assert summary_entry is not None
    assert summary_entry.kind == MemoryKind.SUMMARY
    assert len(summary_entry.source_message_ids) == 4
    assert len(summary_entry.content) > 0


def test_chat_turn_routine():
    mem = AgentMemory.from_config({"persistence": {"sqlite_path": ":memory:"}})

    def mock_responder(pack: MemoryPack) -> str:
        return f"Echoing response for query: {pack.recent_messages[-1].content}"

    pack, reply = mem.chat_turn(
        "Tell me about quantum computing.",
        system_prompt="You are a physics expert.",
        assistant_responder=mock_responder,
    )

    assert reply == "Echoing response for query: Tell me about quantum computing."
    stats = mem.stats()
    # 1 user + 1 assistant message added
    assert stats["message_count"] == 2


def test_maintain_memory_routine():
    mem = AgentMemory.from_config({
        "persistence": {"sqlite_path": ":memory:"},
        "vector": {"enabled": True}
    })

    mem.add_long_term("High importance fact", importance=1.0)
    mem.add_long_term("Low importance fact", importance=0.15)

    assert len(mem.vector) == 2

    res = mem.maintain_memory(decay_factor=0.5, min_importance=0.1)
    # Low importance fact (0.15 * 0.5 = 0.075 < 0.1) should be pruned
    assert res["pruned_count"] == 1
    assert res["remaining_count"] == 1
    assert len(mem.vector) == 1

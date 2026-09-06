"""Summary lifecycle regression tests."""
from agent_memory import AgentMemory
from agent_memory.config.settings import MemorySettings


def test_summarize_old_does_not_reprocess_already_covered_messages():
    settings = MemorySettings.from_dict({
        "window": {"strategy": "summarize_old", "max_tokens": 200, "reserve_for_response": 20},
        "summary": {"backend": "extractive", "trigger_when_tokens_over": 10, "max_summary_tokens": 20, "min_messages_to_summarize": 4},
        "vector": {"enabled": True, "backend": "hash", "dim": 128, "top_k": 3, "persist_embeddings": True},
        "persistence": {"enabled": True, "sqlite_path": ":memory:", "auto_commit": True},
    })
    mem = AgentMemory(settings)
    for i in range(10):
        mem.add_user(f"Conversation item {i}. This contains stable context.")

    first = mem.prepare("stable context")
    assert first.summary
    first_covered = set(first.summary_covers)
    assert first_covered

    second = mem.prepare("stable context")
    assert second.summary
    assert set(second.summary_covers) == first_covered
    assert len(mem.store.get_latest_summary(mem.default_session).source_message_ids) == len(first_covered)
    assert len(mem.store.get_vector_entries()) >= 1
    mem.close()

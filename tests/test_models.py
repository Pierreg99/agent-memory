"""Tests for core data models."""
from agent_memory.core.models import MemoryEntry, MemoryPack, MemoryQuery, Message
from agent_memory.core.types import MemoryKind, Role


def test_message_defaults():
    m = Message(role=Role.USER, content="hi")
    assert m.role == Role.USER
    assert m.content == "hi"
    assert m.id  # auto-generated
    assert m.timestamp > 0
    assert m.metadata == {}


def test_message_string_role_coercion():
    m = Message(role="assistant", content="yo")
    assert m.role == Role.ASSISTANT


def test_memory_entry_defaults():
    e = MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s1", content="fact")
    assert e.kind == MemoryKind.LONG_TERM
    assert e.session_id == "s1"
    assert e.importance == 1.0
    assert e.source_message_ids == []


def test_memory_query_defaults():
    q = MemoryQuery(session_id="s1", query_text="hello")
    assert MemoryKind.LONG_TERM in q.kinds
    assert q.top_k == 5


def test_memory_pack_to_chat_messages_includes_summary_and_facts():
    pack = MemoryPack(
        session_id="s1",
        system_prompt="You are a helpful assistant.",
        recent_messages=[
            Message(role=Role.USER, content="What is the capital of France?"),
            Message(role=Role.ASSISTANT, content="Paris."),
        ],
        summary="Earlier the user introduced themselves.",
        retrieved_facts=[
            MemoryEntry(
                kind=MemoryKind.LONG_TERM,
                session_id="s1",
                content="User lives in Paris.",
            )
        ],
        used_tokens=42,
        budget_tokens=4000,
    )
    msgs = pack.to_chat_messages()
    # First message is synthesized system message
    assert msgs[0]["role"] == "system"
    assert "helpful assistant" in msgs[0]["content"]
    assert "Earlier the user" in msgs[0]["content"]
    assert "User lives in Paris" in msgs[0]["content"]
    # Then the recent messages
    assert msgs[1] == {"role": "user", "content": "What is the capital of France?"}
    assert msgs[2] == {"role": "assistant", "content": "Paris."}


def test_memory_pack_to_chat_messages_no_extras():
    pack = MemoryPack(
        session_id="s1",
        recent_messages=[Message(role=Role.USER, content="hi")],
    )
    msgs = pack.to_chat_messages()
    # No synthesized system message when nothing to put in it
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"

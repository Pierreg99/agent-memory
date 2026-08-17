"""End-to-end tests for the AgentMemory orchestrator."""
from agent_memory import AgentMemory
from agent_memory.config.settings import MemorySettings
from agent_memory.core.types import (
    EmbeddingBackend,
    MemoryKind,
    Role,
    SummarizerBackend,
    WindowStrategy,
)


def _make_mem(**overrides) -> AgentMemory:
    """Build an AgentMemory with a tiny token budget so we can exercise windowing."""
    base = {
        "window": {
            "strategy": "sliding",
            "max_tokens": 80,
            "keep_last_turns": 2,
            "reserve_for_response": 0,
        },
        "tokens": {"backend": "heuristic", "chars_per_token": 4},
        "summary": {
            "backend": "extractive",
            "trigger_when_tokens_over": 60,
            "max_summary_tokens": 30,
            "min_messages_to_summarize": 2,
        },
        "vector": {"enabled": True, "backend": "hash", "dim": 32, "top_k": 3},
        "persistence": {"enabled": True, "sqlite_path": ":memory:"},
    }
    for k, v in overrides.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k].update(v)
        else:
            base[k] = v
    return AgentMemory.from_config(base)


def test_end_to_end_basic_flow():
    mem = _make_mem()
    mem.add_system("You are a helpful assistant.")
    mem.add_user("Hi, I'm Alice.")
    mem.add_assistant("Hello Alice!")
    mem.add_user("I love hiking.")

    mem.add_long_term("User's name is Alice", importance=0.9)
    mem.add_long_term("User enjoys hiking", importance=0.7)

    # Use a query with strong lexical overlap so the hash embedder
    # can retrieve both facts.
    pack = mem.prepare(
        "What hiking activities does Alice enjoy?", system_prompt="You are helpful."
    )

    # System prompt was passed explicitly; the stored system message should
    # not appear in recent_messages.
    assert all(m.role != Role.SYSTEM for m in pack.recent_messages)
    # Retrieved facts should include the hiking fact (lexical overlap)
    contents = [f.content for f in pack.retrieved_facts]
    assert any("hiking" in c.lower() for c in contents)
    # The chat messages should start with a system message that bundles
    # prompt + retrieved facts
    chat = pack.to_chat_messages()
    assert chat[0]["role"] == "system"
    assert "helpful" in chat[0]["content"]
    # Used tokens are within budget
    assert pack.used_tokens <= pack.budget_tokens


def test_windowing_drops_old_messages():
    mem = _make_mem()
    for i in range(10):
        mem.add_user(f"message {i} " + "x" * 20)  # each ~7 tokens
    pack = mem.prepare("any query", system_prompt="You are X.")
    # Budget is 80; with overhead each msg is ~7 tokens, so we should see <= ~11
    assert len(pack.recent_messages) < 10
    # Most recent should always be present
    assert "message 9" in pack.recent_messages[-1].content


def test_summarize_old_strategy_triggers():
    mem = _make_mem(
        window={"strategy": "summarize_old", "max_tokens": 80, "keep_last_turns": 1, "reserve_for_response": 0},
        summary={"trigger_when_tokens_over": 30, "min_messages_to_summarize": 2, "max_summary_tokens": 30},
    )
    for i in range(8):
        mem.add_user(f"User message number {i} with some text")
        mem.add_assistant(f"Assistant reply number {i} with some text")
    pack = mem.prepare("query", system_prompt="You are X.")
    # A summary should have been produced
    assert pack.summary is not None and len(pack.summary) > 0
    # And the summary should be included in the chat message
    chat = pack.to_chat_messages()
    assert any("summary" in c["content"].lower() for c in chat if c["role"] == "system")


def test_persistence_roundtrip():
    mem = _make_mem()
    mem.add_user("remember this")
    mem.add_long_term("User is here", importance=0.5)
    stats = mem.stats()
    assert stats["message_count"] == 1
    assert stats["long_term_count"] == 1


def test_clear_session():
    mem = _make_mem()
    mem.add_user("hello")
    mem.clear_session()
    assert mem.stats()["message_count"] == 0


def test_vector_disabled_works():
    mem = _make_mem(vector={"enabled": False})
    mem.add_user("hi")
    pack = mem.prepare("any")
    assert pack.retrieved_facts == []


def test_persistence_disabled_works():
    mem = _make_mem(persistence={"enabled": False})
    mem.add_user("hi")
    pack = mem.prepare("any")
    assert pack.recent_messages == []  # store is null

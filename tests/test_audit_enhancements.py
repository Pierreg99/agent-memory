"""Additional comprehensive unit tests added during Quality Audit."""
import os
import tempfile
import pytest

from agent_memory import AgentMemory
from agent_memory.config.settings import MemorySettings, WindowConfig, VectorConfig, SummaryConfig
from agent_memory.core.models import MemoryEntry, MemoryQuery, Message
from agent_memory.core.types import MemoryKind, Role, WindowStrategy
from agent_memory.persistence.store import MemoryStore
from agent_memory.summary.summarizer import LLMSummarizer, ResilientSummarizer
from agent_memory.vector.memory import VectorMemory
from agent_memory.window.window_manager import WindowManager


def test_vector_memory_empty_and_zero_top_k():
    cfg = VectorConfig(dim=16)
    vm = VectorMemory(cfg)
    vm.add(MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s1", content="Python memory agent"))

    # Empty query text
    q_empty = MemoryQuery(session_id="s1", query_text="", top_k=5)
    assert vm.query(q_empty) == []

    # Whitespace query text
    q_ws = MemoryQuery(session_id="s1", query_text="   \n \t", top_k=5)
    assert vm.query(q_ws) == []

    # zero or negative top_k
    q_zero = MemoryQuery(session_id="s1", query_text="Python", top_k=0)
    assert vm.query(q_zero) == []

    q_neg = MemoryQuery(session_id="s1", query_text="Python", top_k=-1)
    assert vm.query(q_neg) == []


def test_window_manager_budget_edge_cases():
    # Reserve larger than max_tokens
    config = WindowConfig(max_tokens=100, reserve_for_response=150)
    wm = WindowManager(config)
    assert wm.budget == 1

    msgs = [Message(role=Role.USER, content="Hello world")]
    res = wm.apply(msgs)
    assert res.budget_tokens == 1


def test_llm_summarizer_missing_api_key():
    cfg = SummaryConfig(backend="llm")
    cfg.llm.api_key_env = "NON_EXISTENT_ENV_VAR_12345"
    if "NON_EXISTENT_ENV_VAR_12345" in os.environ:
        del os.environ["NON_EXISTENT_ENV_VAR_12345"]

    summarizer = LLMSummarizer(cfg)
    with pytest.raises(RuntimeError, match="requires NON_EXISTENT_ENV_VAR_12345 in env"):
        summarizer.summarize_text("Test string", max_tokens=50)


def test_resilient_summarizer_falls_back():
    cfg = SummaryConfig(backend="llm")
    cfg.llm.api_key_env = "NON_EXISTENT_ENV_VAR_12345"
    if "NON_EXISTENT_ENV_VAR_12345" in os.environ:
        del os.environ["NON_EXISTENT_ENV_VAR_12345"]

    resilient = ResilientSummarizer(cfg)
    text = "The user likes coffee. Python is a programming language. Unit tests guarantee quality."
    # Should fall back to extractive without raising an exception
    s_text = resilient.summarize_text(text, max_tokens=100)
    assert isinstance(s_text, str)
    assert len(s_text) > 0


def test_persistence_file_store_helper_and_close():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "subdir", "test_memory.db")
        store = MemoryStore.file_store(db_path)
        msg = Message(role=Role.USER, content="Persistent message test")
        store.add_message("sess_test", msg)

        fetched = store.get_messages("sess_test")
        assert len(fetched) == 1
        assert fetched[0].content == "Persistent message test"

        store.close()


def test_agent_memory_clear_session_and_stats():
    mem = AgentMemory.from_config()
    mem.add_user("User statement 1")
    mem.add_assistant("Assistant response 1")
    mem.add_long_term("Fact 1")

    st = mem.stats()
    assert st["message_count"] == 2
    assert st["long_term_count"] == 1
    assert st["vector_count"] == 1

    mem.clear_session()
    st_cleared = mem.stats()
    assert st_cleared["message_count"] == 0
    assert st_cleared["long_term_count"] == 0
    assert st_cleared["vector_count"] == 0

"""Quality hardening regression tests."""
import pytest

from agent_memory.config.settings import TokenConfig, WindowConfig
from agent_memory.core.models import MemoryEntry, MemoryQuery, Message
from agent_memory.core.types import MemoryKind, Role
from agent_memory.summary.summarizer import ExtractiveSummarizer
from agent_memory.window.token_counter import HeuristicTokenCounter
from agent_memory.window.window_manager import WindowManager


def test_window_never_exceeds_hard_budget():
    counter = HeuristicTokenCounter(TokenConfig(chars_per_token=4))
    wm = WindowManager(
        WindowConfig(max_tokens=30, reserve_for_response=10, keep_last_turns=50),
        counter=counter,
    )
    messages = [Message(role=Role.USER, content="x" * 20) for _ in range(20)]
    result = wm.apply(messages)
    assert result.used_tokens <= result.budget_tokens
    assert result.budget_tokens == 20


def test_extract_summarizer_handles_german_and_unicode():
    summarizer = ExtractiveSummarizer()
    text = "Ältere Entscheidung bleibt bestehen. Das Team arbeitet an der nächsten Änderung. Prüfung folgt morgen."
    summary = summarizer.summarize_text(text, max_tokens=30)
    assert summary
    assert "Ältere Entscheidung" in summary or "nächsten Änderung" in summary


def test_memory_models_reject_invalid_values():
    with pytest.raises(ValueError):
        MemoryEntry(kind=MemoryKind.LONG_TERM, session_id="s", content="x", importance=2.0)
    with pytest.raises(ValueError):
        MemoryQuery(session_id="s", query_text="x", top_k=-1)

"""Tests for the summarizer."""
from agent_memory.config.settings import SummaryConfig
from agent_memory.core.models import Message
from agent_memory.core.types import Role
from agent_memory.summary.summarizer import (
    ExtractiveSummarizer,
    build_summarizer,
    to_memory_entry,
)


def _msgs(contents: list[str]) -> list[Message]:
    return [Message(role=Role.USER, content=c) for c in contents]


def test_extractive_summarizer_basic():
    s = ExtractiveSummarizer(
        SummaryConfig(min_messages_to_summarize=2, max_summary_tokens=200)
    )
    msgs = _msgs(
        [
            "The cat sat on the mat. The cat was happy.",
            "The dog ran in the park. The dog loved the park.",
            "Birds sang in the trees. Birds are beautiful.",
        ]
    )
    summary, covered = s.summarize_messages(msgs, max_tokens=200)
    assert summary
    assert len(covered) == len(msgs)
    # Should pick salient sentences — at least one should mention "cat" or "dog" or "birds"
    assert any(w in summary.lower() for w in ["cat", "dog", "birds", "park", "mat", "trees"])


def test_extractive_summarizer_respects_token_budget():
    s = ExtractiveSummarizer(
        SummaryConfig(min_messages_to_summarize=2, max_summary_tokens=20)
    )
    msgs = _msgs(
        [
            "Apples are red and delicious. Oranges are orange and juicy. "
            "Bananas are yellow and long. Grapes are small and sweet.",
            "Pineapples are tropical and spiky. Mangoes are sweet and fibrous. "
            "Kiwis are green and tangy. Watermelons are large and watery.",
        ]
    )
    summary, _ = s.summarize_messages(msgs, max_tokens=20)
    # Heuristic: ~5 chars per token => 20 tokens ~= 100 chars max
    assert len(summary) <= 120


def test_extractive_returns_empty_below_min_messages():
    s = ExtractiveSummarizer(SummaryConfig(min_messages_to_summarize=5))
    msgs = _msgs(["only one"])
    summary, covered = s.summarize_messages(msgs, max_tokens=200)
    assert summary == ""
    assert covered == []


def test_to_memory_entry():
    e = to_memory_entry("summary text", ["m1", "m2"], "sess1")
    assert e.kind.value == "summary"
    assert e.content == "summary text"
    assert e.source_message_ids == ["m1", "m2"]
    assert e.session_id == "sess1"


def test_build_summarizer_extractive():
    s = build_summarizer(SummaryConfig(backend="extractive"))
    assert isinstance(s, ExtractiveSummarizer)


def test_build_summarizer_llm_uses_resilient():
    from agent_memory.summary.summarizer import ResilientSummarizer

    s = build_summarizer(SummaryConfig(backend="llm"))
    assert isinstance(s, ResilientSummarizer)

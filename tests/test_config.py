"""Tests for the configuration loader."""
from agent_memory.config.settings import MemorySettings, load_settings
from agent_memory.core.types import (
    EmbeddingBackend,
    SummarizerBackend,
    WindowStrategy,
)


def test_load_settings_returns_defaults():
    s = load_settings()
    assert isinstance(s, MemorySettings)
    assert s.window.strategy == WindowStrategy.SLIDING
    assert s.summary.backend == SummarizerBackend.EXTRACTIVE
    assert s.vector.backend == EmbeddingBackend.HASH


def test_load_settings_with_overrides():
    s = load_settings(
        {
            "window": {"max_tokens": 8000, "strategy": "truncate_oldest"},
            "summary": {"backend": "llm"},
        }
    )
    assert s.window.max_tokens == 8000
    assert s.window.strategy == WindowStrategy.TRUNCATE_OLDEST
    assert s.summary.backend == SummarizerBackend.LLM
    # Other defaults preserved
    assert s.window.keep_last_turns == 12


def test_settings_to_dict_roundtrip():
    s = load_settings()
    d = s.to_dict()
    s2 = MemorySettings.from_dict(d)
    assert s2 == s

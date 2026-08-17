"""Pluggable token counter.

Provides a fast heuristic counter by default and an optional tiktoken-based
counter for accurate token accounting. The counter caches the per-message
`token_count` field on `Message` to avoid repeated computation.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Protocol

from ..config.settings import TokenConfig
from ..core.models import Message


class TokenCounter(Protocol):
    """Protocol every counter implements."""

    def count_text(self, text: str) -> int: ...
    def count_messages(self, messages: Iterable[Message]) -> int: ...


class HeuristicTokenCounter:
    """Fast character-based token estimator.

    Approximates 1 token ~= `chars_per_token` characters. Good enough for
    windowing decisions when the exact tokenizer isn't known. Per-message
    overhead is added (3 tokens) to roughly approximate role markers.
    """

    PER_MESSAGE_OVERHEAD = 3

    def __init__(self, config: TokenConfig | None = None) -> None:
        self.config = config or TokenConfig()
        self._chars_per_token = max(0.5, float(self.config.chars_per_token))

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        # Use max(1, ...) so a non-empty string always counts as >= 1 token.
        return max(1, int(round(len(text) / self._chars_per_token)))

    def count_messages(self, messages: Iterable[Message]) -> int:
        total = 0
        for m in messages:
            if m.token_count is not None:
                total += m.token_count
            else:
                tc = self.count_text(m.content) + self.PER_MESSAGE_OVERHEAD
                m.token_count = tc
                total += tc
        return total


class TiktokenTokenCounter:
    """Accurate counter backed by tiktoken (optional dependency)."""

    PER_MESSAGE_OVERHEAD = 3

    def __init__(self, config: TokenConfig | None = None) -> None:
        self.config = config or TokenConfig()
        self._enc = _get_tiktoken_encoding(self.config.tiktoken_encoding)

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        return len(self._enc.encode(text))

    def count_messages(self, messages: Iterable[Message]) -> int:
        total = 0
        for m in messages:
            if m.token_count is not None:
                total += m.token_count
            else:
                tc = self.count_text(m.content) + self.PER_MESSAGE_OVERHEAD
                m.token_count = tc
                total += tc
        return total


@lru_cache(maxsize=8)
def _get_tiktoken_encoding(name: str):
    """Lazy-load a tiktoken encoding, raising a helpful error if missing."""
    try:
        import tiktoken  # type: ignore
    except ImportError as e:  # pragma: no cover - optional dep
        raise ImportError(
            "tiktoken is not installed. Either install it "
            "(`pip install tiktoken`) or use HeuristicTokenCounter."
        ) from e
    return tiktoken.get_encoding(name)


def build_counter(config: TokenConfig | None = None) -> TokenCounter:
    """Factory: pick a counter based on config."""
    cfg = config or TokenConfig()
    backend = (cfg.backend or "heuristic").lower()
    if backend == "tiktoken":
        return TiktokenTokenCounter(cfg)
    return HeuristicTokenCounter(cfg)

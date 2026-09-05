"""Summarization engine.

Two backends are provided:

* ExtractiveSummarizer - a fast, no-LLM summarizer that picks the most
  important sentences from a block of text using a small keyword-scoring
  heuristic. Always available, zero external dependencies.

* LLMSummarizer - a thin adapter that calls an OpenAI-compatible chat
  completions endpoint. Falls back to a clear NotImplementedError if the
  `requests` library is unavailable or the call fails, so callers can
  gracefully fall back to extractive.

A `Summarizer` Protocol is exported so users can plug in their own
implementation (Claude, local LLM, etc.).
"""
from __future__ import annotations

import os
import re
from collections import Counter
from collections.abc import Iterable
from typing import Protocol

import requests

from ..config.settings import LLMSummaryConfig, SummaryConfig
from ..core.models import MemoryEntry, Message
from ..core.types import MemoryKind

# English stopwords for the extractive heuristic. Small list by design.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to",
    "in", "on", "at", "by", "for", "with", "as", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "i", "you", "he", "she", "we", "they", "them", "my", "your", "our",
    "have", "has", "had", "do", "does", "did", "not", "no", "so", "up",
    "out", "from", "into", "over", "under", "about", "than", "also", "just",
    "can", "could", "should", "would", "will", "may", "might", "must",
}


class Summarizer(Protocol):
    """Pluggable summarizer interface."""

    def summarize_text(self, text: str, max_tokens: int) -> str: ...
    def summarize_messages(
        self, messages: list[Message], max_tokens: int
    ) -> tuple[str, list[str]]: ...


# ---------------------------------------------------------------------------
# Extractive summarizer
# ---------------------------------------------------------------------------


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = _SENT_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"\b\w+\b", text) if w.lower() not in _STOPWORDS]


class ExtractiveSummarizer:
    """Extractive summarizer using keyword-frequency scoring.

    For each sentence, score = sum of (1 + log(freq(word))) for each
    non-stopword. Top-N sentences are kept in their original order, where
    N is chosen to fit within `max_tokens` (using the heuristic counter).
    """

    def __init__(self, config: SummaryConfig | None = None) -> None:
        self.config = config or SummaryConfig()
        # Local import to avoid a circular import
        from ..window.token_counter import HeuristicTokenCounter

        self._counter = HeuristicTokenCounter()

    def summarize_text(self, text: str, max_tokens: int) -> str:
        sentences = _split_sentences(text)
        if not sentences:
            return ""
        if len(sentences) == 1:
            return sentences[0]

        # Score each sentence by keyword frequency
        words = _tokenize(text)
        freq = Counter(words)

        scores: list[tuple[int, float]] = []  # (index, score)
        for i, s in enumerate(sentences):
            toks = _tokenize(s)
            if not toks:
                scores.append((i, 0.0))
                continue
            score = sum(1.0 + (0 if freq[t] <= 1 else (freq[t] - 1) ** 0.5) for t in toks)
            # Normalize by length so long sentences don't dominate unfairly
            scores.append((i, score / max(1, len(toks)) ** 0.5))

        # Pick top sentences by score, then order them by their original index
        scores.sort(key=lambda x: x[1], reverse=True)
        chosen: list[tuple[int, str]] = []
        used = 0
        for idx, _ in scores:
            s = sentences[idx]
            tc = self._counter.count_text(s)
            if used + tc > max_tokens and chosen:
                continue
            chosen.append((idx, s))
            used += tc
            if used >= max_tokens:
                break
        chosen.sort(key=lambda x: x[0])
        return " ".join(s for _, s in chosen)

    def summarize_messages(
        self, messages: list[Message], max_tokens: int
    ) -> tuple[str, list[str]]:
        if not messages:
            return "", []
        if len(messages) < self.config.min_messages_to_summarize:
            return "", []

        # Join messages into one block for sentence-level scoring
        joined = "\n".join(f"{m.role.value}: {m.content}" for m in messages)
        summary = self.summarize_text(joined, max_tokens)
        covered_ids = [m.id for m in messages]
        return summary, covered_ids


# ---------------------------------------------------------------------------
# LLM summarizer
# ---------------------------------------------------------------------------


class LLMSummarizer:
    """OpenAI-compatible chat-completions summarizer.

    Reads the API key from `LLMSummaryConfig.api_key_env`. If the key is
    missing or the request fails, raises a RuntimeError so the caller can
    fall back to the extractive summarizer.
    """

    SYSTEM_PROMPT = (
        "You are a concise summarizer. Compress the following conversation "
        "into a short, factual summary that preserves decisions, names, "
        "numbers, and unresolved questions. Output plain text only."
    )

    def __init__(self, config: SummaryConfig | None = None) -> None:
        self.config = config or SummaryConfig()
        self.llm_cfg: LLMSummaryConfig = self.config.llm

    def summarize_text(self, text: str, max_tokens: int) -> str:
        api_key = os.environ.get(self.llm_cfg.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"LLM summarizer requires {self.llm_cfg.api_key_env} in env"
            )
        payload = {
            "model": self.llm_cfg.model,
            "temperature": self.llm_cfg.temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
        try:
            resp = requests.post(
                self.llm_cfg.endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # pragma: no cover - network
            raise RuntimeError(f"LLM summarization failed: {e}") from e
        return data["choices"][0]["message"]["content"].strip()

    def summarize_messages(
        self, messages: list[Message], max_tokens: int
    ) -> tuple[str, list[str]]:
        if not messages:
            return "", []
        joined = "\n".join(f"{m.role.value}: {m.content}" for m in messages)
        summary = self.summarize_text(joined, max_tokens)
        return summary, [m.id for m in messages]


# ---------------------------------------------------------------------------
# Composite / fallback
# ---------------------------------------------------------------------------


class ResilientSummarizer:
    """Tries LLM first, falls back to extractive on any error.

    This is the default summarizer used by the orchestrator when
    `summary.backend == llm`, so the system remains functional even without
    network or API access.
    """

    def __init__(self, config: SummaryConfig | None = None) -> None:
        self.config = config or SummaryConfig()
        self.llm = LLMSummarizer(self.config)
        self.extractive = ExtractiveSummarizer(self.config)

    def summarize_text(self, text: str, max_tokens: int) -> str:
        try:
            return self.llm.summarize_text(text, max_tokens)
        except Exception:  # noqa: BLE001 - fallback to extractive on any error (network, auth, rate limit)
            return self.extractive.summarize_text(text, max_tokens)

    def summarize_messages(
        self, messages: list[Message], max_tokens: int
    ) -> tuple[str, list[str]]:
        # LLM path
        try:
            return self.llm.summarize_messages(messages, max_tokens)
        except Exception:  # noqa: BLE001 - fallback to extractive on any error (network, auth, rate limit)
            return self.extractive.summarize_messages(messages, max_tokens)


def build_summarizer(config: SummaryConfig) -> Summarizer:
    """Factory: build the right summarizer for a given config."""
    if config.backend.value == "llm":
        return ResilientSummarizer(config)
    return ExtractiveSummarizer(config)


def to_memory_entry(
    summary: str,
    covered_ids: Iterable[str],
    session_id: str,
) -> MemoryEntry:
    """Wrap a summary into a MemoryEntry for persistence."""
    return MemoryEntry(
        kind=MemoryKind.SUMMARY,
        session_id=session_id,
        content=summary,
        source_message_ids=list(covered_ids),
    )

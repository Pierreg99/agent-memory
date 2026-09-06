"""Pluggable summarization backends with deterministic fallback behavior."""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import Iterable, Optional, Protocol

import requests

from ..config.settings import LLMSummaryConfig, SummaryConfig
from ..core.models import MemoryEntry, Message
from ..core.types import MemoryKind, Role


_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to",
    "in", "on", "at", "by", "for", "with", "as", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "i", "you", "he", "she", "we", "they", "them", "my", "your", "our",
    "have", "has", "had", "do", "does", "did", "not", "no", "so", "up", "out",
    "from", "into", "over", "under", "about", "than", "also", "just", "can",
    "could", "should", "would", "will", "may", "might", "must",
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "einem",
    "einen", "eines", "und", "oder", "aber", "wenn", "dann", "von", "zu", "in",
    "im", "auf", "an", "am", "für", "mit", "als", "ist", "sind", "war", "waren",
    "sein", "nicht", "kein", "keine", "ich", "du", "er", "sie", "wir", "ihr", "mich",
    "dich", "mein", "dein", "unser", "euer", "hat", "haben", "wird", "werden", "auch",
    "nur", "noch", "über", "unter", "dass", "wie", "was",
}


class Summarizer(Protocol):
    def summarize_text(self, text: str, max_tokens: int) -> str: ...
    def summarize_messages(self, messages: list[Message], max_tokens: int) -> tuple[str, list[str]]: ...


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [p.strip() for p in _SENT_SPLIT.split(text) if p.strip()]


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"\b\w+\b", text, flags=re.UNICODE) if w.lower() not in _STOPWORDS]


class ExtractiveSummarizer:
    """Lightweight extractive summarizer using multilingual keyword scoring."""

    def __init__(self, config: Optional[SummaryConfig] = None) -> None:
        self.config = config or SummaryConfig()
        from ..window.token_counter import HeuristicTokenCounter
        self._counter = HeuristicTokenCounter()

    def summarize_text(self, text: str, max_tokens: int) -> str:
        if max_tokens <= 0:
            return ""
        sentences = _split_sentences(text)
        if not sentences:
            return ""
        if len(sentences) == 1:
            return sentences[0]

        freq = Counter(_tokenize(text))
        scores: list[tuple[int, float]] = []
        for i, sentence in enumerate(sentences):
            tokens = _tokenize(sentence)
            if not tokens:
                scores.append((i, 0.0))
                continue
            score = sum(1.0 + ((freq[token] - 1) ** 0.5 if freq[token] > 1 else 0.0) for token in tokens)
            scores.append((i, score / max(1, len(tokens)) ** 0.5))

        scores.sort(key=lambda x: x[1], reverse=True)
        chosen: list[tuple[int, str]] = []
        used = 0
        for idx, _ in scores:
            sentence = sentences[idx]
            token_count = self._counter.count_text(sentence)
            if used + token_count > max_tokens and chosen:
                continue
            chosen.append((idx, sentence))
            used += token_count
            if used >= max_tokens:
                break
        chosen.sort(key=lambda x: x[0])
        return " ".join(sentence for _, sentence in chosen)

    def summarize_messages(self, messages: list[Message], max_tokens: int) -> tuple[str, list[str]]:
        if not messages or len(messages) < self.config.min_messages_to_summarize:
            return "", []
        joined = "\n".join(f"{m.role.value}: {m.content}" for m in messages)
        return self.summarize_text(joined, max_tokens), [m.id for m in messages]


class LLMSummarizer:
    """OpenAI-compatible chat-completions summarizer."""

    SYSTEM_PROMPT = (
        "You are a concise summarizer. Compress the following conversation "
        "into a short, factual summary that preserves decisions, names, "
        "numbers, and unresolved questions. Preserve the input language where "
        "practical. Output plain text only."
    )

    def __init__(self, config: Optional[SummaryConfig] = None) -> None:
        self.config = config or SummaryConfig()
        self.llm_cfg: LLMSummaryConfig = self.config.llm

    def summarize_text(self, text: str, max_tokens: int) -> str:
        api_key = os.environ.get(self.llm_cfg.api_key_env)
        if not api_key:
            raise RuntimeError(f"LLM summarizer requires environment variable {self.llm_cfg.api_key_env} to be set")
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
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:  # pragma: no cover - network
            raise RuntimeError(f"LLM summarization failed: {e}") from e

    def summarize_messages(self, messages: list[Message], max_tokens: int) -> tuple[str, list[str]]:
        if not messages:
            return "", []
        joined = "\n".join(f"{m.role.value}: {m.content}" for m in messages)
        return self.summarize_text(joined, max_tokens), [m.id for m in messages]


class ResilientSummarizer:
    """Try LLM first and deterministically fall back to extractive."""

    def __init__(self, config: Optional[SummaryConfig] = None) -> None:
        self.config = config or SummaryConfig()
        self.llm = LLMSummarizer(self.config)
        self.extractive = ExtractiveSummarizer(self.config)

    def summarize_text(self, text: str, max_tokens: int) -> str:
        try:
            return self.llm.summarize_text(text, max_tokens)
        except Exception:
            return self.extractive.summarize_text(text, max_tokens)

    def summarize_messages(self, messages: list[Message], max_tokens: int) -> tuple[str, list[str]]:
        try:
            return self.llm.summarize_messages(messages, max_tokens)
        except Exception:
            return self.extractive.summarize_messages(messages, max_tokens)


def build_summarizer(config: SummaryConfig) -> Summarizer:
    return ResilientSummarizer(config) if config.backend.value == "llm" else ExtractiveSummarizer(config)


def to_memory_entry(summary: str, covered_ids: Iterable[str], session_id: str) -> MemoryEntry:
    return MemoryEntry(
        kind=MemoryKind.SUMMARY,
        session_id=session_id,
        role=Role.SUMMARY,
        content=summary,
        source_message_ids=list(covered_ids),
    )

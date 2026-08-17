"""Common enums and type aliases used across the agent memory system."""
from __future__ import annotations

from enum import Enum
from typing import Literal


class Role(str, Enum):
    """Chat roles in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SUMMARY = "summary"  # Synthetic role for summarized memory


class MemoryKind(str, Enum):
    """Kinds of memory an agent can store."""

    SHORT_TERM = "short_term"      # Recent conversation turns
    LONG_TERM = "long_term"        # Facts to remember across sessions
    SUMMARY = "summary"            # Compressed view of older turns
    WORKING = "working"            # Scratch / intermediate state


class WindowStrategy(str, Enum):
    """Strategies for managing the conversation context window."""

    SLIDING = "sliding"            # Keep the most recent N turns
    TRUNCATE_OLDEST = "truncate_oldest"  # Drop oldest messages first
    SUMMARIZE_OLD = "summarize_old"      # Compress oldest into a summary


class SummarizerBackend(str, Enum):
    """Pluggable summarizer backends."""

    EXTRACTIVE = "extractive"
    LLM = "llm"


class EmbeddingBackend(str, Enum):
    """Pluggable embedding backends."""

    HASH = "hash"                  # Deterministic, no deps
    SENTENCE_TRANSFORMERS = "sentence_transformers"  # Optional


RoleLiteral = Literal["system", "user", "assistant", "tool", "summary"]
MemoryKindLiteral = Literal["short_term", "long_term", "summary", "working"]
WindowStrategyLiteral = Literal["sliding", "truncate_oldest", "summarize_old"]

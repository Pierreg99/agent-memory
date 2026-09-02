"""Pydantic data models for messages, memory entries, and query results."""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from .types import MemoryKind, Role


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> float:
    return time.time()


class Message(BaseModel):
    """A single chat message."""

    id: str = Field(default_factory=_new_id)
    role: Role
    content: str
    timestamp: float = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_count: Optional[int] = None  # Cached token count, computed lazily

    def model_post_init(self, _ctx: Any) -> None:
        # Normalize role if it came in as a string
        if isinstance(self.role, str):
            self.role = Role(self.role)


class MemoryEntry(BaseModel):
    """A piece of memory stored in the system.

    Could be a raw message, a summary, or a long-term fact. The kind field
    discriminates so storage and retrieval can be specialized per type.
    """

    id: str = Field(default_factory=_new_id)
    kind: MemoryKind
    session_id: str
    role: Optional[Role] = None
    content: str
    embedding: Optional[list[float]] = None
    source_message_ids: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=_now)
    importance: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Temporal & Knowledge Graph fields
    entity: Optional[str] = None
    attribute: Optional[str] = None
    valid_from: Optional[float] = None
    valid_until: Optional[float] = None
    is_superseded: bool = False
    superseded_by: Optional[str] = None

    def model_post_init(self, _ctx: Any) -> None:
        if isinstance(self.kind, str):
            self.kind = MemoryKind(self.kind)
        if isinstance(self.role, str) and self.role is not None:
            self.role = Role(self.role)
        if self.valid_from is None:
            self.valid_from = self.created_at


class MemoryQuery(BaseModel):
    """A query against the memory system."""

    session_id: str
    query_text: str
    top_k: int = 5
    kinds: list[MemoryKind] = Field(
        default_factory=lambda: [MemoryKind.LONG_TERM, MemoryKind.SUMMARY]
    )
    min_importance: float = 0.0
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    include_superseded: bool = False


class MemoryPack(BaseModel):
    """The complete bundle an LLM needs to respond to a turn.

    The orchestrator produces one of these per request. It contains the
    context-windowed recent messages, any prior summary, and the top-k
    long-term facts retrieved for the current query.
    """

    session_id: str
    system_prompt: Optional[str] = None
    recent_messages: list[Message] = Field(default_factory=list)
    summary: Optional[str] = None
    summary_covers: list[str] = Field(default_factory=list)
    retrieved_facts: list[MemoryEntry] = Field(default_factory=list)
    used_tokens: int = 0
    budget_tokens: int = 0

    def to_chat_messages(self) -> list[dict[str, str]]:
        """Render this pack as the messages array for an OpenAI-style chat API.

        Order: [system(with summary + facts), ...recent_messages]
        """
        out: list[dict[str, str]] = []
        if self.system_prompt or self.summary or self.retrieved_facts:
            parts: list[str] = []
            if self.system_prompt:
                parts.append(self.system_prompt)
            if self.summary:
                parts.append(f"Conversation so far (summary):\n{self.summary}")
            if self.retrieved_facts:
                facts = "\n".join(
                    f"- [{f.kind.value}] {f.content}" for f in self.retrieved_facts
                )
                parts.append(f"Relevant long-term memories:\n{facts}")
            out.append({"role": "system", "content": "\n\n".join(parts)})
        for m in self.recent_messages:
            out.append({"role": m.role.value, "content": m.content})
        return out

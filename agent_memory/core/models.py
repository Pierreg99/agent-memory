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
    token_count: Optional[int] = Field(default=None, ge=0)

    def model_post_init(self, _ctx: Any) -> None:
        if isinstance(self.role, str):
            self.role = Role(self.role)


class MemoryEntry(BaseModel):
    """A raw message, summary, long-term fact, or other memory entry."""

    id: str = Field(default_factory=_new_id)
    kind: MemoryKind
    session_id: str
    role: Optional[Role] = None
    content: str
    embedding: Optional[list[float]] = None
    source_message_ids: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=_now)
    importance: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, _ctx: Any) -> None:
        if isinstance(self.kind, str):
            self.kind = MemoryKind(self.kind)
        if isinstance(self.role, str):
            self.role = Role(self.role)


class MemoryQuery(BaseModel):
    """A query against the memory system."""

    session_id: str
    query_text: str
    top_k: int = Field(default=5, ge=0)
    kinds: list[MemoryKind] = Field(default_factory=lambda: [MemoryKind.LONG_TERM, MemoryKind.SUMMARY])
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata_filter: dict[str, Any] = Field(default_factory=dict)


class MemoryPack(BaseModel):
    """The complete bundle an LLM needs to respond to a turn."""

    session_id: str
    system_prompt: Optional[str] = None
    recent_messages: list[Message] = Field(default_factory=list)
    summary: Optional[str] = None
    summary_covers: list[str] = Field(default_factory=list)
    retrieved_facts: list[MemoryEntry] = Field(default_factory=list)
    used_tokens: int = Field(default=0, ge=0)
    budget_tokens: int = Field(default=0, ge=0)

    def to_chat_messages(self) -> list[dict[str, str]]:
        """Render the pack as OpenAI-style chat messages."""
        out: list[dict[str, str]] = []
        if self.system_prompt or self.summary or self.retrieved_facts:
            parts: list[str] = []
            if self.system_prompt:
                parts.append(self.system_prompt)
            if self.summary:
                parts.append(f"Conversation so far (summary):\n{self.summary}")
            if self.retrieved_facts:
                facts = "\n".join(f"- [{f.kind.value}] {f.content}" for f in self.retrieved_facts)
                parts.append(f"Relevant long-term memories:\n{facts}")
            out.append({"role": "system", "content": "\n\n".join(parts)})
        for message in self.recent_messages:
            out.append({"role": message.role.value, "content": message.content})
        return out

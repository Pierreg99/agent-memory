"""Top-level orchestrator composing all memory subsystems."""
from __future__ import annotations

import threading
import time
from typing import Any, Iterable, Optional, Union

from .config.settings import MemorySettings, load_settings
from .core.models import MemoryEntry, MemoryPack, MemoryQuery, Message
from .core.types import MemoryKind, Role, WindowStrategy
from .persistence.store import MemoryStore
from .summary.summarizer import Summarizer, build_summarizer, to_memory_entry
from .vector.memory import VectorMemory
from .window.token_counter import TokenCounter, build_counter
from .window.window_manager import WindowManager


class AgentMemory:
    """Composed agent memory system with durable semantic recall."""

    def __init__(self, settings: MemorySettings, counter: Optional[TokenCounter] = None,
                 window: Optional[WindowManager] = None, summarizer: Optional[Summarizer] = None,
                 store: Optional[MemoryStore] = None, vector: Optional[VectorMemory] = None) -> None:
        self.settings = settings
        self.counter = counter or build_counter(settings.tokens)
        self.window = window or WindowManager(settings.window, self.counter)
        self.summarizer = summarizer or build_summarizer(settings.summary)
        self.store = store or (
            MemoryStore(path=settings.persistence.sqlite_path, auto_commit=settings.persistence.auto_commit)
            if settings.persistence.enabled else _NullStore()
        )
        self.vector = vector or (VectorMemory(settings.vector) if settings.vector.enabled else None)
        self._lifecycle_lock = threading.RLock()

        if settings.persistence.enabled and self.vector is not None and settings.vector.persist_embeddings:
            self.vector.restore(self.store.get_vector_entries())
        if settings.persistence.enabled and settings.session.clear_on_start:
            self.clear_session()
        if settings.persistence.enabled and settings.retention.enabled and settings.retention.run_on_start:
            self.purge_expired()

    @classmethod
    def from_config(cls, overrides: Optional[dict[str, Any]] = None) -> "AgentMemory":
        return cls(settings=load_settings(overrides))

    @classmethod
    def from_yaml(cls, path: str) -> "AgentMemory":
        return cls(settings=MemorySettings.from_yaml(path))

    @property
    def default_session(self) -> str:
        return self.settings.session.default_id

    def clear_session(self, session_id: Optional[str] = None) -> None:
        sid = session_id or self.default_session
        self.store.clear_session(sid)
        if self.vector is not None:
            self.vector.clear_session(sid)

    def export_session(self, session_id: Optional[str] = None) -> dict[str, Any]:
        return self.store.export_session(session_id or self.default_session)

    def purge_expired(self, now: Optional[float] = None) -> dict[str, int]:
        if not self.settings.retention.enabled or self.settings.retention.days <= 0:
            return {"messages": 0, "summaries": 0, "long_term": 0, "memory_vectors": 0}
        cutoff = (time.time() if now is None else float(now)) - self.settings.retention.days * 86400
        counts = self.store.purge_older_than(cutoff)
        if self.vector is not None:
            self.vector.clear()
            if self.settings.vector.persist_embeddings:
                self.vector.restore(self.store.get_vector_entries())
        return counts

    def add(self, role: Union[Role, str], content: str, session_id: Optional[str] = None,
            metadata: Optional[dict[str, Any]] = None) -> Message:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("message content must be a non-empty string")
        sid = session_id or self.default_session
        resolved = role if isinstance(role, Role) else Role(role)
        msg = Message(role=resolved, content=content, metadata=metadata or {})
        self.store.add_message(sid, msg)
        return msg

    def add_user(self, content: str, session_id: Optional[str] = None, **meta: Any) -> Message:
        return self.add(Role.USER, content, session_id, meta or None)

    def add_assistant(self, content: str, session_id: Optional[str] = None, **meta: Any) -> Message:
        return self.add(Role.ASSISTANT, content, session_id, meta or None)

    def add_system(self, content: str, session_id: Optional[str] = None, **meta: Any) -> Message:
        return self.add(Role.SYSTEM, content, session_id, meta or None)

    def add_long_term(self, content: str, session_id: Optional[str] = None,
                      importance: float = 1.0, metadata: Optional[dict[str, Any]] = None) -> MemoryEntry:
        if not content or not content.strip():
            raise ValueError("long-term memory content must be a non-empty string")
        if not 0.0 <= importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")
        sid = session_id or self.default_session
        entry = MemoryEntry(kind=MemoryKind.LONG_TERM, session_id=sid, role=Role.SYSTEM,
                            content=content, importance=importance, metadata=metadata or {})
        self.store.add_long_term(entry)
        if self.vector is not None:
            self.vector.add(entry)
            if self.settings.vector.persist_embeddings:
                self.store.add_vector_entry(entry)
        return entry

    def add_many_long_term(self, facts: Iterable[str], session_id: Optional[str] = None,
                           importance: float = 1.0) -> list[MemoryEntry]:
        return [self.add_long_term(f, session_id, importance) for f in facts]

    def prepare(self, query_text: str, session_id: Optional[str] = None,
                system_prompt: Optional[str] = None) -> MemoryPack:
        if not isinstance(query_text, str) or not query_text.strip():
            raise ValueError("query_text must be a non-empty string")
        sid = session_id or self.default_session
        all_messages = self.store.get_messages(sid)

        summary_entry = self.store.get_latest_summary(sid)
        summary_text = summary_entry.content if summary_entry else None
        summary_covers = list(summary_entry.source_message_ids) if summary_entry else []

        total_tokens = self.counter.count_messages(all_messages)
        trigger = self.settings.summary.trigger_when_tokens_over
        if (self.settings.window.strategy == WindowStrategy.SUMMARIZE_OLD
                and total_tokens > trigger
                and len(all_messages) >= self.settings.summary.min_messages_to_summarize):
            with self._lifecycle_lock:
                current_summary = self.store.get_latest_summary(sid)
                covered = set(current_summary.source_message_ids) if current_summary else set()
                candidate_messages = [m for m in all_messages if m.id not in covered]
                if len(candidate_messages) >= self.settings.summary.min_messages_to_summarize:
                    n_recent = max(1, len(candidate_messages) // 4)
                    to_summarize = candidate_messages[:-n_recent] if n_recent < len(candidate_messages) else candidate_messages
                    new_summary, covered_ids = self.summarizer.summarize_messages(
                        to_summarize, self.settings.summary.max_summary_tokens
                    )
                    if new_summary and covered_ids:
                        entry = to_memory_entry(new_summary, covered_ids, sid)
                        self.store.add_summary(sid, entry)
                        if self.vector is not None:
                            self.vector.add(entry)
                            if self.settings.vector.persist_embeddings:
                                self.store.add_vector_entry(entry)
                        summary_text = new_summary
                        summary_covers = covered_ids

        result = self.window.apply(all_messages, system_prompt=system_prompt)
        recent = [m for m in result.kept if not system_prompt or m.role != Role.SYSTEM]

        retrieved: list[MemoryEntry] = []
        if self.vector is not None:
            q = MemoryQuery(session_id=sid, query_text=query_text, top_k=self.settings.vector.top_k,
                            kinds=[MemoryKind.LONG_TERM, MemoryKind.SUMMARY], min_importance=0.0)
            retrieved = self.vector.query(q)

        recent, summary_text, retrieved, used_tokens = self._fit_pack_to_budget(
            recent, summary_text, retrieved, system_prompt
        )

        return MemoryPack(session_id=sid, system_prompt=system_prompt, recent_messages=recent,
                          summary=summary_text, summary_covers=summary_covers,
                          retrieved_facts=retrieved, used_tokens=used_tokens,
                          budget_tokens=self.window.budget)

    def _render_system_context(self, system_prompt: Optional[str], summary: Optional[str],
                               retrieved: list[MemoryEntry]) -> str:
        parts: list[str] = []
        if system_prompt:
            parts.append(system_prompt)
        if summary:
            parts.append(f"Conversation so far (summary):\n{summary}")
        if retrieved:
            facts = "\n".join(f"- [{f.kind.value}] {f.content}" for f in retrieved)
            parts.append(f"Relevant long-term memories:\n{facts}")
        return "\n\n".join(parts)

    def _fit_pack_to_budget(self, recent: list[Message], summary: Optional[str],
                            retrieved: list[MemoryEntry], system_prompt: Optional[str]):
        """Fit the fully rendered prompt to the configured prompt-side budget."""
        budget = self.window.budget

        def total_tokens() -> int:
            system = self._render_system_context(system_prompt, summary, retrieved)
            system_tokens = self.counter.count_text(system) + (3 if system else 0)
            return system_tokens + self.counter.count_messages(recent)

        # Retrieval is supplemental, so trim least-ranked facts first.
        while retrieved and total_tokens() > budget:
            retrieved.pop()
        # Preserve the newest conversational turns as long as possible.
        while recent and total_tokens() > budget:
            recent.pop(0)
        # A summary is useful but must not violate the ceiling.
        if summary and total_tokens() > budget:
            fixed = self._render_system_context(system_prompt, None, retrieved)
            available = max(0, budget - (self.counter.count_text(fixed) + (3 if fixed else 0))
                            - self.counter.count_messages(recent))
            summary = _truncate_text(summary, self.counter, max_tokens=available)
        # A pathological oversized system prompt is the final case. Truncate it
        # rather than returning a prompt larger than the configured ceiling.
        if system_prompt and total_tokens() > budget:
            fixed = self._render_system_context(None, summary, retrieved)
            available = max(0, budget - (self.counter.count_text(fixed) + (3 if fixed else 0))
                            - self.counter.count_messages(recent))
            system_prompt = _truncate_text(system_prompt, self.counter, max_tokens=available)
            # Preserve the caller's reference semantics by replacing local value
            # only for the final rendered budget calculation.
            rendered = self._render_system_context(system_prompt, summary, retrieved)
        used = total_tokens()
        return recent, summary, retrieved, min(used, budget)

    def stats(self, session_id: Optional[str] = None) -> dict[str, Any]:
        sid = session_id or self.default_session
        msgs = self.store.get_messages(sid)
        long_term = self.store.get_long_term(sid, limit=10_000)
        return {"session_id": sid, "message_count": len(msgs), "long_term_count": len(long_term),
                "vector_count": len(self.vector) if self.vector else 0,
                "total_tokens": self.counter.count_messages(msgs), "budget_tokens": self.window.budget}

    def close(self) -> None:
        close = getattr(self.store, "close", None)
        if callable(close):
            close()


class _NullStore:
    def add_message(self, *a: Any, **kw: Any) -> None: ...
    def add_messages(self, *a: Any, **kw: Any) -> None: ...
    def get_messages(self, *a: Any, **kw: Any) -> list[Message]: return []
    def add_summary(self, *a: Any, **kw: Any) -> None: ...
    def get_latest_summary(self, *a: Any, **kw: Any) -> Optional[MemoryEntry]: return None
    def add_long_term(self, *a: Any, **kw: Any) -> None: ...
    def get_long_term(self, *a: Any, **kw: Any) -> list[MemoryEntry]: return []
    def add_vector_entry(self, *a: Any, **kw: Any) -> None: ...
    def get_vector_entries(self, *a: Any, **kw: Any) -> list[MemoryEntry]: return []
    def clear_session(self, *a: Any, **kw: Any) -> None: ...
    def purge_older_than(self, *a: Any, **kw: Any) -> dict[str, int]:
        return {"messages": 0, "summaries": 0, "long_term": 0, "memory_vectors": 0}
    def export_session(self, *a: Any, **kw: Any) -> dict[str, Any]:
        return {"session_id": a[0] if a else "default", "messages": [], "long_term": [], "vectors": [], "latest_summary": None}
    def close(self) -> None: ...


def _truncate_text(text: str, counter: TokenCounter, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    if counter.count_text(text) <= max_tokens:
        return text
    words = text.split()
    lo, hi = 0, len(words)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = " ".join(words[:mid])
        if counter.count_text(candidate) <= max_tokens:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return best

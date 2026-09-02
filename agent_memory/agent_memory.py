"""Top-level orchestrator that composes all memory subsystems.

`AgentMemory` is the only object an application needs to interact with.
It wires together the token counter, the window manager, the summarizer,
the vector memory, and the persistent store, and exposes a small,
ergonomic API:

    mem = AgentMemory.from_config()                 # load defaults
    mem.add_user("Hello")                            # ingest a turn
    pack = mem.prepare("How should I respond?")     # build the LLM context
    chat = pack.to_chat_messages()                   # hand to an LLM SDK
    mem.add_assistant(chat_reply)                    # close the loop

The orchestrator is also responsible for triggering summarization when
the conversation grows past `summary.trigger_when_tokens_over`.
"""
from __future__ import annotations

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
    """Composed agent memory system."""

    def __init__(
        self,
        settings: MemorySettings,
        counter: Optional[TokenCounter] = None,
        window: Optional[WindowManager] = None,
        summarizer: Optional[Summarizer] = None,
        store: Optional[MemoryStore] = None,
        vector: Optional[VectorMemory] = None,
        working_entries: Optional[list[MemoryEntry]] = None,
    ) -> None:
        self.settings = settings
        self.counter = counter or build_counter(settings.tokens)
        self.window = window or WindowManager(settings.window, self.counter)
        self.summarizer = summarizer or build_summarizer(settings.summary)
        self.store = store or (
            MemoryStore(
                path=settings.persistence.sqlite_path,
                auto_commit=settings.persistence.auto_commit,
            )
            if settings.persistence.enabled
            else _NullStore()
        )
        self.vector = vector or (
            VectorMemory(settings.vector) if settings.vector.enabled else None
        )
        self._working_entries = working_entries if working_entries is not None else []

    # ---- factories -------------------------------------------------------

    @classmethod
    def from_config(
        cls,
        overrides: Optional[dict[str, Any]] = None,
    ) -> "AgentMemory":
        """Build an AgentMemory from defaults + an optional overrides dict."""
        settings = load_settings(overrides)
        return cls(settings=settings)

    @classmethod
    def from_yaml(cls, path: str) -> "AgentMemory":
        settings = MemorySettings.from_yaml(path)
        return cls(settings=settings)

    # ---- eviction -------------------------------------------------------

    def evict_stale(
        self,
        session_id: Optional[str] = None,
        min_importance: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> dict[str, int]:
        """Evict stale or low-importance facts from vector memory and persistent store."""
        min_imp = (
            min_importance
            if min_importance is not None
            else self.settings.vector.min_importance_threshold
        )
        vec_evicted = 0
        if self.vector is not None:
            vec_evicted = self.vector.evict(
                session_id=session_id,
                min_importance=min_imp,
                max_entries=self.settings.vector.max_entries,
                current_time=current_time,
            )
        store_evicted = 0
        if hasattr(self.store, "evict_stale"):
            store_evicted = self.store.evict_stale(
                session_id=session_id,
                min_importance=min_imp,
                half_life_days=self.settings.vector.half_life_days,
                decay_enabled=self.settings.vector.decay_enabled,
                current_time=current_time,
            )
        return {"vector_evicted": vec_evicted, "store_evicted": store_evicted}

    # ---- session helpers ------------------------------------------------

    @property
    def default_session(self) -> str:
        return self.settings.session.default_id

    def clear_session(self, session_id: Optional[str] = None) -> None:
        sid = session_id or self.default_session
        self.store.clear_session(sid)
        if self.vector is not None:
            self.vector.clear()

    # ---- ingest ---------------------------------------------------------

    def add(
        self,
        role: Union[Role, str],
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Message:
        """Add a single message to the conversation and persist it."""
        sid = session_id or self.default_session
        msg = Message(
            role=Role(role) if not isinstance(role, Role) else role,
            content=content,
            metadata=metadata or {},
        )
        self.store.add_message(sid, msg)
        return msg

    def add_user(
        self,
        content: str,
        session_id: Optional[str] = None,
        **meta: Any,
    ) -> Message:
        return self.add(Role.USER, content, session_id, meta or None)

    def add_assistant(
        self,
        content: str,
        session_id: Optional[str] = None,
        **meta: Any,
    ) -> Message:
        return self.add(Role.ASSISTANT, content, session_id, meta or None)

    def add_system(
        self,
        content: str,
        session_id: Optional[str] = None,
        **meta: Any,
    ) -> Message:
        return self.add(Role.SYSTEM, content, session_id, meta or None)

    def create_sub_agent_memory(
        self,
        role_name: str,
        can_write_long_term: bool = False,
        can_write_persistent: bool = True,
    ) -> "AgentMemory":
        """Spawn a child AgentMemory instance with restricted permissions for sub-agent execution."""
        sub_settings = self.settings.model_copy(deep=True)
        sub_settings.agent_role.role_name = role_name
        sub_settings.agent_role.can_write_long_term = can_write_long_term
        sub_settings.agent_role.can_write_persistent = can_write_persistent
        return AgentMemory(
            settings=sub_settings,
            counter=self.counter,
            window=self.window,
            summarizer=self.summarizer,
            store=self.store,
            vector=self.vector,
            working_entries=self._working_entries,
        )

    def add_long_term(
        self,
        content: str,
        session_id: Optional[str] = None,
        importance: float = 1.0,
        entity: Optional[str] = None,
        attribute: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Store a long-term fact and add it to vector memory if enabled."""
        if not self.settings.agent_role.can_write_long_term:
            raise PermissionError(
                f"Agent role '{self.settings.agent_role.role_name}' does not have permission to write long-term memory."
            )

        sid = session_id or self.default_session
        meta = dict(metadata or {})
        ent = entity or meta.get("entity")
        attr = attribute or meta.get("attribute")

        entry = MemoryEntry(
            kind=MemoryKind.LONG_TERM,
            session_id=sid,
            role=Role.SYSTEM,
            content=content,
            importance=importance,
            entity=ent,
            attribute=attr,
            metadata=meta,
        )
        if self.settings.agent_role.can_write_persistent:
            self.store.add_long_term(entry)
        if self.vector is not None:
            self.vector.add(entry)
        return entry

    def add_working(
        self,
        content: str,
        session_id: Optional[str] = None,
        importance: float = 0.5,
        entity: Optional[str] = None,
        attribute: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Store intermediate sub-agent state in working memory without polluting long-term RAG."""
        sid = session_id or self.default_session
        meta = dict(metadata or {})
        meta["agent_role"] = self.settings.agent_role.role_name
        ent = entity or meta.get("entity")
        attr = attribute or meta.get("attribute")

        entry = MemoryEntry(
            kind=MemoryKind.WORKING,
            session_id=sid,
            role=Role.SYSTEM,
            content=content,
            importance=importance,
            entity=ent,
            attribute=attr,
            metadata=meta,
        )
        self._working_entries.append(entry)
        if self.settings.agent_role.can_write_persistent:
            self.store.add_long_term(entry)
        return entry

    def get_working_entries(self, session_id: Optional[str] = None) -> list[MemoryEntry]:
        """Retrieve working memory entries for the session."""
        sid = session_id or self.default_session
        result_map: dict[str, MemoryEntry] = {}
        if hasattr(self.store, "get_working"):
            for e in self.store.get_working(sid):
                result_map[e.id] = e
        for e in self._working_entries:
            if e.session_id == sid and e.id not in result_map:
                result_map[e.id] = e
        return list(result_map.values())

    def promote_working_to_long_term(
        self,
        entry_ids: Union[str, list[str]],
        session_id: Optional[str] = None,
        importance: Optional[float] = None,
    ) -> list[MemoryEntry]:
        """Promote specified working memory entry/entries into permanent long-term memory."""
        if not self.settings.agent_role.can_write_long_term:
            raise PermissionError(
                f"Agent role '{self.settings.agent_role.role_name}' does not have permission to promote working memory to long-term memory."
            )

        sid = session_id or self.default_session
        ids = [entry_ids] if isinstance(entry_ids, str) else list(entry_ids)
        working_all = self.get_working_entries(sid)
        promoted: list[MemoryEntry] = []

        for w_entry in working_all:
            if w_entry.id in ids:
                imp = importance if importance is not None else w_entry.importance
                lt_entry = self.add_long_term(
                    content=w_entry.content,
                    session_id=sid,
                    importance=imp,
                    entity=w_entry.entity,
                    attribute=w_entry.attribute,
                    metadata=dict(w_entry.metadata),
                )
                promoted.append(lt_entry)

        return promoted

    def add_many_long_term(
        self,
        facts: Iterable[str],
        session_id: Optional[str] = None,
        importance: float = 1.0,
    ) -> list[MemoryEntry]:
        return [self.add_long_term(f, session_id, importance) for f in facts]

    # ---- context assembly ----------------------------------------------

    def prepare(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> MemoryPack:
        """Assemble a `MemoryPack` ready to hand to an LLM.

        Steps:
        1. Load all messages for the session from the store.
        2. If the conversation exceeds the summary trigger threshold AND
           strategy is `summarize_old`, summarize the oldest half.
        3. Apply the window manager to pick the recent messages that fit.
        4. Retrieve top-k long-term facts relevant to `query_text`.
        5. Return everything bundled as a MemoryPack.
        """
        sid = session_id or self.default_session
        all_messages = self.store.get_messages(sid)

        # Optionally summarize the oldest chunk
        summary_entry = self.store.get_latest_summary(sid)
        summary_text: Optional[str] = None
        summary_covers: list[str] = []
        if summary_entry is not None:
            summary_text = summary_entry.content
            summary_covers = list(summary_entry.source_message_ids)

        # Summarize-old strategy: if total tokens over threshold, compress oldest
        total_tokens = self.counter.count_messages(all_messages)
        trigger = self.settings.summary.trigger_when_tokens_over
        if (
            self.settings.window.strategy == WindowStrategy.SUMMARIZE_OLD
            and total_tokens > trigger
            and len(all_messages) >= self.settings.summary.min_messages_to_summarize
        ):
            # Skip the most recent quarter when choosing what to summarize.
            n_recent = max(1, len(all_messages) // 4)
            to_summarize = all_messages[:-n_recent] if n_recent < len(all_messages) else all_messages
            new_summary, covered_ids = self.summarizer.summarize_messages(
                to_summarize, self.settings.summary.max_summary_tokens
            )
            if new_summary:
                entry = to_memory_entry(new_summary, covered_ids, sid)
                self.store.add_summary(sid, entry)
                summary_text = new_summary
                summary_covers = covered_ids

        # Apply windowing
        result = self.window.apply(all_messages, system_prompt=system_prompt)
        recent = result.kept
        # When the caller passes an explicit system_prompt, any stored system
        # messages are redundant — drop them so the LLM only sees one system
        # message at the head of the prompt.
        if system_prompt:
            recent = [m for m in recent if m.role != Role.SYSTEM]

        # Retrieve long-term facts
        retrieved: list[MemoryEntry] = []
        if self.vector is not None:
            q = MemoryQuery(
                session_id=sid,
                query_text=query_text,
                top_k=self.settings.vector.top_k,
                kinds=[MemoryKind.LONG_TERM, MemoryKind.SUMMARY],
                min_importance=0.0,
            )
            retrieved = self.vector.query(q)

        return MemoryPack(
            session_id=sid,
            system_prompt=system_prompt,
            recent_messages=recent,
            summary=summary_text,
            summary_covers=summary_covers,
            retrieved_facts=retrieved,
            used_tokens=result.used_tokens,
            budget_tokens=result.budget_tokens,
        )

    # ---- introspection --------------------------------------------------

    def stats(self, session_id: Optional[str] = None) -> dict[str, Any]:
        sid = session_id or self.default_session
        msgs = self.store.get_messages(sid)
        long_term = self.store.get_long_term(sid, limit=10_000)
        return {
            "session_id": sid,
            "message_count": len(msgs),
            "long_term_count": len(long_term),
            "vector_count": len(self.vector) if self.vector else 0,
            "total_tokens": self.counter.count_messages(msgs),
            "budget_tokens": self.window.budget,
        }


class _NullStore:
    """No-op store used when persistence is disabled.

    Implements only the methods AgentMemory actually calls, so we don't
    have to maintain two parallel APIs.
    """

    def add_message(self, *a: Any, **kw: Any) -> None: ...
    def add_messages(self, *a: Any, **kw: Any) -> None: ...
    def get_messages(self, *a: Any, **kw: Any) -> list[Message]:
        return []

    def add_summary(self, *a: Any, **kw: Any) -> None: ...
    def get_latest_summary(self, *a: Any, **kw: Any) -> Optional[MemoryEntry]:
        return None

    def add_long_term(self, entry: MemoryEntry) -> None: ...
    def get_long_term(self, *a: Any, **kw: Any) -> list[MemoryEntry]:
        return []

    def clear_session(self, *a: Any, **kw: Any) -> None: ...

"""SQLite-backed persistent memory store.

Messages, summaries, long-term facts, and vector embeddings are persisted so
an AgentMemory instance can be reconstructed without losing semantic recall.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from ..core.models import MemoryEntry, Message
from ..core.types import MemoryKind, Role


_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    ts          REAL NOT NULL,
    metadata    TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_session
    ON messages(session_id, ts);

CREATE TABLE IF NOT EXISTS summaries (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    content         TEXT NOT NULL,
    source_ids      TEXT NOT NULL,
    created_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_summaries_session
    ON summaries(session_id, created_at);

CREATE TABLE IF NOT EXISTS long_term (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    importance  REAL NOT NULL DEFAULT 1.0,
    metadata    TEXT,
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_long_term_session
    ON long_term(session_id, kind);

CREATE TABLE IF NOT EXISTS memory_vectors (
    entry_id    TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    role        TEXT,
    importance  REAL NOT NULL DEFAULT 1.0,
    metadata    TEXT,
    embedding   TEXT NOT NULL,
    source_ids  TEXT,
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_vectors_session
    ON memory_vectors(session_id, created_at);
"""


class MemoryStore:
    """Thread-safe SQLite memory store with durable semantic indexes."""

    def __init__(self, path: str = ":memory:", auto_commit: bool = True) -> None:
        self.path = path
        self.auto_commit = auto_commit
        self._local = threading.local()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            if auto_commit:
                conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
            timeout=30.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.executescript(_SCHEMA)
        if self.auto_commit:
            conn.commit()
        return conn

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = self._connect()
            self._local.conn = conn
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            if self.auto_commit:
                conn.commit()

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ---- messages -------------------------------------------------------

    def add_message(self, session_id: str, message: Message) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO messages "
                "(id, session_id, role, content, ts, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    message.id,
                    session_id,
                    message.role.value,
                    message.content,
                    message.timestamp,
                    json.dumps(message.metadata or {}, ensure_ascii=False),
                ),
            )

    def add_messages(self, session_id: str, messages: Iterable[Message]) -> None:
        with self._conn() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO messages "
                "(id, session_id, role, content, ts, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        m.id,
                        session_id,
                        m.role.value,
                        m.content,
                        m.timestamp,
                        json.dumps(m.metadata or {}, ensure_ascii=False),
                    )
                    for m in messages
                ],
            )

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> list[Message]:
        with self._conn() as conn:
            query = "SELECT id, role, content, ts, metadata FROM messages WHERE session_id = ? ORDER BY ts ASC"
            params: tuple[Any, ...] = (session_id,)
            if limit is not None:
                query += " LIMIT ?"
                params += (max(0, int(limit)),)
            cur = conn.execute(query, params)
            return [_row_to_message(r) for r in cur.fetchall()]

    def clear_messages(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

    # ---- summaries ------------------------------------------------------

    def add_summary(self, session_id: str, entry: MemoryEntry) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO summaries "
                "(id, session_id, content, source_ids, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    entry.id,
                    session_id,
                    entry.content,
                    json.dumps(entry.source_message_ids, ensure_ascii=False),
                    entry.created_at,
                ),
            )

    def get_latest_summary(self, session_id: str) -> Optional[MemoryEntry]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, content, source_ids, created_at FROM summaries "
                "WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                (session_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return MemoryEntry(
                id=row["id"],
                kind=MemoryKind.SUMMARY,
                session_id=session_id,
                role=Role.SUMMARY,
                content=row["content"],
                source_message_ids=json.loads(row["source_ids"] or "[]"),
                created_at=row["created_at"],
            )

    # ---- long-term facts -----------------------------------------------

    def add_long_term(self, entry: MemoryEntry) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO long_term "
                "(id, session_id, kind, content, importance, metadata, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.session_id,
                    entry.kind.value,
                    entry.content,
                    entry.importance,
                    json.dumps(entry.metadata or {}, ensure_ascii=False),
                    entry.created_at,
                ),
            )

    def get_long_term(self, session_id: str, limit: int = 100) -> list[MemoryEntry]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, kind, content, importance, metadata, created_at "
                "FROM long_term WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, max(0, int(limit))),
            )
            return [_row_to_long_term(session_id, r) for r in cur.fetchall()]

    # ---- vector persistence --------------------------------------------

    def add_vector_entry(self, entry: MemoryEntry) -> None:
        """Persist a fully embedded memory entry."""
        if entry.embedding is None:
            raise ValueError("cannot persist a vector entry without embedding")
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory_vectors "
                "(entry_id, session_id, kind, content, role, importance, metadata, embedding, source_ids, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.session_id,
                    entry.kind.value,
                    entry.content,
                    entry.role.value if entry.role else None,
                    entry.importance,
                    json.dumps(entry.metadata or {}, ensure_ascii=False),
                    json.dumps(entry.embedding),
                    json.dumps(entry.source_message_ids, ensure_ascii=False),
                    entry.created_at,
                ),
            )

    def get_vector_entries(self, session_id: Optional[str] = None) -> list[MemoryEntry]:
        with self._conn() as conn:
            if session_id:
                cur = conn.execute(
                    "SELECT entry_id, session_id, kind, content, role, importance, metadata, embedding, source_ids, created_at "
                    "FROM memory_vectors WHERE session_id = ? ORDER BY created_at ASC",
                    (session_id,),
                )
            else:
                cur = conn.execute(
                    "SELECT entry_id, session_id, kind, content, role, importance, metadata, embedding, source_ids, created_at "
                    "FROM memory_vectors ORDER BY created_at ASC"
                )
            return [_row_to_vector_entry(r) for r in cur.fetchall()]

    # ---- lifecycle / privacy -------------------------------------------

    def clear_session(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM summaries WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM long_term WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM memory_vectors WHERE session_id = ?", (session_id,))

    def purge_older_than(self, cutoff_timestamp: float) -> dict[str, int]:
        """Delete all memory records older than a UNIX timestamp."""
        cutoff = float(cutoff_timestamp)
        with self._conn() as conn:
            tables = (
                ("messages", "ts"),
                ("summaries", "created_at"),
                ("long_term", "created_at"),
                ("memory_vectors", "created_at"),
            )
            counts: dict[str, int] = {}
            for table, column in tables:
                cur = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} < ?", (cutoff,))
                counts[table] = int(cur.fetchone()[0])
                conn.execute(f"DELETE FROM {table} WHERE {column} < ?", (cutoff,))
            return counts

    def export_session(self, session_id: str) -> dict[str, Any]:
        """Export one session as JSON-serializable dictionaries."""
        messages = self.get_messages(session_id)
        long_term = self.get_long_term(session_id, limit=100_000)
        vectors = self.get_vector_entries(session_id)
        latest = self.get_latest_summary(session_id)
        return {
            "session_id": session_id,
            "exported_at": time.time(),
            "messages": [m.model_dump(mode="json") for m in messages],
            "long_term": [e.model_dump(mode="json") for e in long_term],
            "vectors": [e.model_dump(mode="json") for e in vectors],
            "latest_summary": latest.model_dump(mode="json") if latest else None,
        }

    @staticmethod
    def file_store(path: str | Path) -> "MemoryStore":
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return MemoryStore(path=str(p), auto_commit=True)


def _row_to_message(row: sqlite3.Row) -> Message:
    return Message(
        id=row["id"],
        role=Role(row["role"]),
        content=row["content"],
        timestamp=row["ts"],
        metadata=json.loads(row["metadata"] or "{}"),
    )


def _row_to_long_term(session_id: str, row: sqlite3.Row) -> MemoryEntry:
    return MemoryEntry(
        id=row["id"],
        kind=MemoryKind(row["kind"]),
        session_id=session_id,
        content=row["content"],
        importance=row["importance"],
        metadata=json.loads(row["metadata"] or "{}"),
        created_at=row["created_at"],
    )


def _row_to_vector_entry(row: sqlite3.Row) -> MemoryEntry:
    role = row["role"]
    return MemoryEntry(
        id=row["entry_id"],
        kind=MemoryKind(row["kind"]),
        session_id=row["session_id"],
        role=Role(role) if role else None,
        content=row["content"],
        embedding=[float(x) for x in json.loads(row["embedding"] or "[]")],
        source_message_ids=json.loads(row["source_ids"] or "[]"),
        importance=row["importance"],
        metadata=json.loads(row["metadata"] or "{}"),
        created_at=row["created_at"],
    )

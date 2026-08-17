"""SQLite-backed persistent memory store.

Tables
------
* messages    - one row per chat message (id, session_id, role, content, ts)
* summaries   - one row per generated summary (covers a list of msg ids)
* long_term   - long-term facts (id, session_id, content, importance, metadata)

Embeddings for vector memory are NOT stored here; VectorMemory holds them
in-process. This keeps the schema simple and the dependency surface zero.

When `sqlite_path == ":memory:"` the store is ephemeral. Pass a file path
to enable persistence across processes.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Optional

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
"""


class MemoryStore:
    """Thread-safe SQLite memory store.

    A single connection is used per thread (Python's sqlite3 connections
    are not safe to share across threads by default). For multi-threaded
    server use, consider wrapping this in a per-request connection pool.
    """

    def __init__(self, path: str = ":memory:", auto_commit: bool = True) -> None:
        self.path = path
        self.auto_commit = auto_commit
        self._local = threading.local()
        # Eagerly initialize the schema on the main thread
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            if auto_commit:
                conn.commit()

    # ---- connection management ------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        # Apply schema to every new connection — per-thread connections may be
        # opened on threads other than the one that constructed the store.
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
        finally:
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
                "(id, session_id, role, content, ts, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    message.id,
                    session_id,
                    message.role.value,
                    message.content,
                    message.timestamp,
                    json.dumps(message.metadata or {}),
                ),
            )

    def add_messages(self, session_id: str, messages: Iterable[Message]) -> None:
        with self._conn() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO messages "
                "(id, session_id, role, content, ts, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        m.id,
                        session_id,
                        m.role.value,
                        m.content,
                        m.timestamp,
                        json.dumps(m.metadata or {}),
                    )
                    for m in messages
                ],
            )

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> list[Message]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, role, content, ts, metadata FROM messages "
                "WHERE session_id = ? ORDER BY ts ASC"
                + (" LIMIT ?" if limit else ""),
                (session_id, limit) if limit else (session_id,),
            )
            return [_row_to_message(r) for r in cur.fetchall()]

    def clear_messages(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

    # ---- summaries ------------------------------------------------------

    def add_summary(
        self,
        session_id: str,
        entry: MemoryEntry,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO summaries "
                "(id, session_id, content, source_ids, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    entry.id,
                    session_id,
                    entry.content,
                    json.dumps(entry.source_message_ids),
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
                source_message_ids=json.loads(row["source_ids"]),
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
                    json.dumps(entry.metadata or {}),
                    entry.created_at,
                ),
            )

    def get_long_term(self, session_id: str, limit: int = 100) -> list[MemoryEntry]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, kind, content, importance, metadata, created_at "
                "FROM long_term WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            )
            return [_row_to_long_term(session_id, r) for r in cur.fetchall()]

    def clear_session(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM summaries WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM long_term WHERE session_id = ?", (session_id,))

    # ---- file path helper ----------------------------------------------

    @staticmethod
    def file_store(path: str | Path) -> "MemoryStore":
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return MemoryStore(path=str(p), auto_commit=True)


def _row_to_message(row: sqlite3.Row) -> Message:
    meta = json.loads(row["metadata"] or "{}")
    return Message(
        id=row["id"],
        role=Role(row["role"]),
        content=row["content"],
        timestamp=row["ts"],
        metadata=meta,
    )


def _row_to_long_term(session_id: str, row: sqlite3.Row) -> MemoryEntry:
    meta = json.loads(row["metadata"] or "{}")
    return MemoryEntry(
        id=row["id"],
        kind=MemoryKind(row["kind"]),
        session_id=session_id,
        content=row["content"],
        importance=row["importance"],
        metadata=meta,
        created_at=row["created_at"],
    )

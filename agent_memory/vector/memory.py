"""Vector-based long-term memory (RAG component)."""
from __future__ import annotations

import threading
from typing import Iterable, Optional

import numpy as np

from ..config.settings import VectorConfig
from ..core.models import MemoryEntry, MemoryQuery
from .embeddings import Embedder, build_embedder


class VectorMemory:
    """In-process vector index with durable-entry reconstruction support.

    The index remains O(N), which is appropriate for small deployments. A
    persistent MemoryStore can now provide the entries and embeddings so a
    process restart does not discard semantic recall.
    """

    def __init__(self, config: VectorConfig, embedder: Optional[Embedder] = None) -> None:
        self.config = config
        self.embedder = embedder or build_embedder(config)
        if self.embedder.dim != self.config.dim:
            self.config.dim = self.embedder.dim
        self._entries: list[MemoryEntry] = []
        self._vectors: list[np.ndarray] = []
        self._index: dict[str, int] = {}
        self._lock = threading.RLock()

    # ---- mutation ------------------------------------------------------

    def add(self, entry: MemoryEntry) -> None:
        """Embed and upsert an entry."""
        if entry.embedding is None:
            entry.embedding = self.embedder.embed_entry(entry)
        self.add_embedded(entry)

    def add_embedded(self, entry: MemoryEntry) -> None:
        """Insert an entry whose embedding is already materialized."""
        vec = np.asarray(entry.embedding or [], dtype=np.float32)
        if vec.ndim != 1 or len(vec) != self.config.dim:
            raise ValueError(
                f"embedding dimension mismatch: expected {self.config.dim}, got {len(vec)}"
            )
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        entry.embedding = vec.tolist()
        with self._lock:
            existing = self._index.get(entry.id)
            if existing is not None:
                self._entries[existing] = entry
                self._vectors[existing] = vec
            else:
                self._index[entry.id] = len(self._entries)
                self._entries.append(entry)
                self._vectors.append(vec)

    def add_many(self, entries: Iterable[MemoryEntry]) -> None:
        for entry in entries:
            self.add(entry)

    def restore(self, entries: Iterable[MemoryEntry]) -> int:
        """Restore pre-embedded entries and return the number loaded."""
        count = 0
        for entry in entries:
            if entry.embedding is None:
                continue
            self.add_embedded(entry)
            count += 1
        return count

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._vectors.clear()
            self._index.clear()

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            keep = [
                (entry, vec)
                for entry, vec in zip(self._entries, self._vectors)
                if entry.session_id != session_id
            ]
            self._entries = [entry for entry, _ in keep]
            self._vectors = [vec for _, vec in keep]
            self._index = {entry.id: i for i, entry in enumerate(self._entries)}

    # ---- query ---------------------------------------------------------

    def query(self, q: MemoryQuery) -> list[MemoryEntry]:
        """Return up to q.top_k entries most similar to q.query_text."""
        if not q.query_text.strip() or q.top_k <= 0:
            return []
        with self._lock:
            if not self._entries:
                return []
            query_vec = np.asarray(self.embedder.embed_text(q.query_text), dtype=np.float32)
            norm = float(np.linalg.norm(query_vec))
            if norm > 0:
                query_vec = query_vec / norm
            matrix = np.stack(self._vectors, axis=0)
            sims = matrix @ query_vec

            candidates: list[tuple[int, float]] = []
            kinds_set = set(q.kinds) if q.kinds else None
            for i, entry in enumerate(self._entries):
                if q.session_id and entry.session_id != q.session_id:
                    continue
                if kinds_set and entry.kind not in kinds_set:
                    continue
                if entry.importance < q.min_importance:
                    continue
                if q.metadata_filter and not all(
                    entry.metadata.get(k) == v for k, v in q.metadata_filter.items()
                ):
                    continue
                if sims[i] < self.config.min_similarity:
                    continue
                candidates.append((i, float(sims[i])))

            candidates.sort(key=lambda x: (-x[1], self._entries[x[0]].created_at))
            return [self._entries[i] for i, _ in candidates[: q.top_k]]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

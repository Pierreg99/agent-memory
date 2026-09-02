"""Vector-based long-term memory (RAG component).

Stores MemoryEntry objects, embeds them, and retrieves the top-k most
similar entries to a query by cosine similarity. Supports metadata
filtering and importance-based filtering.
"""
from __future__ import annotations

import time
from typing import Iterable, Optional

import numpy as np

from ..config.settings import VectorConfig
from ..core.models import MemoryEntry, MemoryQuery
from ..core.types import MemoryKind
from .embeddings import Embedder, build_embedder


class VectorMemory:
    """In-process vector store with optional metadata filtering.

    Vectors and metadata live in a single list; queries are O(N) over
    entries. This is appropriate for thousands-of-entries scale. For
    larger scale, swap in FAISS / Qdrant / pgvector behind the same
    `add` / `query` interface.
    """

    def __init__(self, config: VectorConfig, embedder: Optional[Embedder] = None) -> None:
        self.config = config
        self.embedder = embedder or build_embedder(config)
        # Ensure embedder dim matches config
        if self.embedder.dim != self.config.dim:
            # Prefer the embedder's actual dim when it's a real model
            self.config.dim = self.embedder.dim
        self._entries: list[MemoryEntry] = []
        self._vectors: list[np.ndarray] = []

    # ---- mutation --------------------------------------------------------

    def add(self, entry: MemoryEntry) -> None:
        """Embed and store an entry."""
        if entry.kind == MemoryKind.LONG_TERM and entry.entity and entry.attribute:
            for e in self._entries:
                if (
                    e.kind == MemoryKind.LONG_TERM
                    and e.session_id == entry.session_id
                    and e.entity == entry.entity
                    and e.attribute == entry.attribute
                    and not e.is_superseded
                    and e.id != entry.id
                ):
                    e.is_superseded = True
                    e.superseded_by = entry.id
                    e.valid_until = entry.created_at

        if entry.embedding is None:
            entry.embedding = self.embedder.embed_entry(entry)
        vec = np.asarray(entry.embedding, dtype=np.float32)
        # Normalize for cosine similarity via dot product
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        entry.embedding = vec.tolist()
        self._entries.append(entry)
        self._vectors.append(vec)

    def add_many(self, entries: Iterable[MemoryEntry]) -> None:
        for e in entries:
            self.add(e)

    def clear(self) -> None:
        self._entries.clear()
        self._vectors.clear()

    # ---- decay & eviction ------------------------------------------------

    def compute_effective_importance(
        self,
        entry: MemoryEntry,
        current_time: Optional[float] = None,
    ) -> float:
        """Compute the entry's importance adjusted for exponential time decay if enabled."""
        if not self.config.decay_enabled or self.config.half_life_days <= 0:
            return entry.importance
        now = current_time if current_time is not None else time.time()
        age_seconds = max(0.0, now - entry.created_at)
        age_days = age_seconds / 86400.0
        decay_factor = 0.5 ** (age_days / self.config.half_life_days)
        return entry.importance * decay_factor

    def evict(
        self,
        session_id: Optional[str] = None,
        min_importance: Optional[float] = None,
        max_entries: Optional[int] = None,
        current_time: Optional[float] = None,
    ) -> int:
        """Evict stale entries below min_importance threshold or to satisfy max_entries capacity."""
        min_imp = min_importance if min_importance is not None else self.config.min_importance_threshold
        max_e = max_entries if max_entries is not None else self.config.max_entries

        now = current_time if current_time is not None else time.time()

        keep_indices: list[int] = []
        for i, entry in enumerate(self._entries):
            if session_id is not None and entry.session_id != session_id:
                keep_indices.append(i)
                continue
            eff_imp = self.compute_effective_importance(entry, current_time=now)
            if eff_imp >= min_imp:
                keep_indices.append(i)

        if max_e is not None and len(keep_indices) > max_e:
            keep_indices.sort(
                key=lambda idx: self.compute_effective_importance(self._entries[idx], current_time=now),
                reverse=True,
            )
            keep_indices = keep_indices[:max_e]

        keep_set = set(keep_indices)
        evicted_count = len(self._entries) - len(keep_set)
        if evicted_count > 0:
            self._entries = [self._entries[i] for i in range(len(self._entries)) if i in keep_set]
            self._vectors = [self._vectors[i] for i in range(len(self._vectors)) if i in keep_set]

        return evicted_count

    # ---- query -----------------------------------------------------------

    def query(
        self,
        q: MemoryQuery,
        current_time: Optional[float] = None,
    ) -> list[MemoryEntry]:
        """Return up to q.top_k entries most similar to q.query_text."""
        if not self._entries:
            return []

        query_vec = np.asarray(self.embedder.embed_text(q.query_text), dtype=np.float32)
        norm = float(np.linalg.norm(query_vec))
        if norm > 0:
            query_vec = query_vec / norm

        matrix = np.stack(self._vectors, axis=0)  # (N, D)
        sims = matrix @ query_vec  # (N,)

        now = current_time if current_time is not None else time.time()

        # Apply filters
        candidates: list[tuple[int, float]] = []
        kinds_set = set(q.kinds) if q.kinds else None
        for i, entry in enumerate(self._entries):
            if kinds_set and entry.kind not in kinds_set:
                continue
            if not q.include_superseded and entry.is_superseded:
                continue
            eff_imp = self.compute_effective_importance(entry, current_time=now)
            if eff_imp < q.min_importance or eff_imp < self.config.min_importance_threshold:
                continue
            if q.metadata_filter:
                if not all(entry.metadata.get(k) == v for k, v in q.metadata_filter.items()):
                    continue
            if sims[i] < self.config.min_similarity:
                continue
            candidates.append((i, float(sims[i])))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top = candidates[: max(0, int(q.top_k))]
        return [self._entries[i] for i, _ in top]

    def __len__(self) -> int:
        return len(self._entries)

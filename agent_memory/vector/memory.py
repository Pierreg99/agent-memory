"""Vector-based long-term memory (RAG component).

Stores MemoryEntry objects, embeds them, and retrieves the top-k most
similar entries to a query by cosine similarity. Supports metadata
filtering and importance-based filtering.
"""
from __future__ import annotations

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

    def decay_importance(self, factor: float = 0.95) -> None:
        """Decay the importance score of all entries by a constant factor."""
        for entry in self._entries:
            entry.importance *= factor

    def prune_memories(self, min_importance: float = 0.1) -> int:
        """Prune entries whose importance falls below min_importance.

        Returns the count of pruned memories.
        """
        pruned_count = 0
        new_entries: list[MemoryEntry] = []
        new_vectors: list[np.ndarray] = []
        for entry, vec in zip(self._entries, self._vectors):
            if entry.importance < min_importance:
                pruned_count += 1
            else:
                new_entries.append(entry)
                new_vectors.append(vec)
        self._entries = new_entries
        self._vectors = new_vectors
        return pruned_count

    # ---- query -----------------------------------------------------------

    def query(self, q: MemoryQuery) -> list[MemoryEntry]:
        """Return up to q.top_k entries most similar to q.query_text."""
        if not self._entries:
            return []

        query_vec = np.asarray(self.embedder.embed_text(q.query_text), dtype=np.float32)
        norm = float(np.linalg.norm(query_vec))
        if norm > 0:
            query_vec = query_vec / norm

        matrix = np.stack(self._vectors, axis=0)  # (N, D)
        sims = matrix @ query_vec  # (N,)

        # Precompute query keywords for hybrid lexical-vector matching boost
        q_words = set(w.lower() for w in q.query_text.split() if len(w) >= 3)

        # Apply filters & hybrid lexical scoring boost
        candidates: list[tuple[int, float]] = []
        kinds_set = set(q.kinds) if q.kinds else None
        for i, entry in enumerate(self._entries):
            if kinds_set and entry.kind not in kinds_set:
                continue
            if entry.importance < q.min_importance:
                continue
            if q.metadata_filter:
                if not all(entry.metadata.get(k) == v for k, v in q.metadata_filter.items()):
                    continue

            score = float(sims[i])
            if q_words:
                content_words = set(w.lower() for w in entry.content.split())
                overlap = len(q_words & content_words)
                if overlap > 0:
                    # Hybrid boost: scale score up based on exact word matches
                    score += 0.3 * (overlap / len(q_words))

            if score < self.config.min_similarity:
                continue
            candidates.append((i, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top = candidates[: max(0, int(q.top_k))]
        return [self._entries[i] for i, _ in top]

    def __len__(self) -> int:
        return len(self._entries)

"""Pluggable embedding backends.

The default backend is a deterministic, dependency-free hash embedder. It
uses signed feature hashing over token n-grams to produce a fixed-dim
vector. Vectors are not semantically rich, but they preserve lexical
similarity well enough for small agent memory use cases and are
guaranteed to be reproducible across processes.

A sentence-transformers adapter is provided as an opt-in alternative.
"""
from __future__ import annotations

import hashlib
import re
from typing import Protocol

from ..config.settings import VectorConfig
from ..core.models import MemoryEntry


class Embedder(Protocol):
    """Protocol for any embedder implementation."""

    dim: int

    def embed_text(self, text: str) -> list[float]: ...
    def embed_entry(self, entry: MemoryEntry) -> list[float]: ...


# ---------------------------------------------------------------------------
# Hash embedder (default)
# ---------------------------------------------------------------------------


_TOKEN_RE = re.compile(r"\b\w+\b")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _ngrams(tokens: list[str], n_min: int = 1, n_max: int = 2) -> list[str]:
    out: list[str] = []
    for n in range(n_min, n_max + 1):
        for i in range(len(tokens) - n + 1):
            out.append(" ".join(tokens[i : i + n]))
    return out


class HashEmbedder:
    """Deterministic feature-hashing embedder.

    For each (token, n) pair we compute a stable bucket index and a sign
    from a hash digest. The resulting vector is L2-normalized so cosine
    similarity reduces to a dot product.
    """

    def __init__(self, config: VectorConfig | None = None) -> None:
        self.config = config or VectorConfig()
        self.dim = int(self.config.dim)

    def _hash_pair(self, token: str, n: int) -> tuple[int, float]:
        h = hashlib.blake2b(f"{n}:{token}".encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "big") % self.dim
        sign = 1.0 if (h[4] & 1) else -1.0
        return idx, sign

    def embed_text(self, text: str) -> list[float]:
        toks = _tokenize(text)
        grams = _ngrams(toks, 1, 2)
        vec = [0.0] * self.dim
        if not grams:
            return vec
        for g in grams:
            idx, sign = self._hash_pair(g, len(g.split()))
            vec[idx] += sign
        # L2 normalize
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_entry(self, entry: MemoryEntry) -> list[float]:
        return self.embed_text(entry.content)


# ---------------------------------------------------------------------------
# Sentence-transformers adapter (optional)
# ---------------------------------------------------------------------------


class SentenceTransformersEmbedder:
    """Adapter for the `sentence-transformers` package.

    Lazy-imports the library on first use so this module remains
    importable without the optional dependency.
    """

    def __init__(self, config: VectorConfig | None = None) -> None:
        self.config = config or VectorConfig()
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as e:  # pragma: no cover - optional dep
            raise ImportError(
                "sentence-transformers is not installed. Either install it "
                "(`pip install sentence-transformers`) or use HashEmbedder."
            ) from e
        self._model = SentenceTransformer(self.config.model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed_text(self, text: str) -> list[float]:
        vec = self._model.encode(text, normalize_embeddings=True)
        return [float(x) for x in vec]

    def embed_entry(self, entry: MemoryEntry) -> list[float]:
        return self.embed_text(entry.content)


def build_embedder(config: VectorConfig) -> Embedder:
    """Factory: pick an embedder based on config."""
    backend = (config.backend.value if hasattr(config.backend, "value") else str(config.backend)).lower()
    if backend == "sentence_transformers":
        return SentenceTransformersEmbedder(config)
    return HashEmbedder(config)

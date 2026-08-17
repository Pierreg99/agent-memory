"""Pydantic-backed settings loader for the agent memory system."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from ..core.types import (
    EmbeddingBackend,
    SummarizerBackend,
    WindowStrategy,
)


class WindowConfig(BaseModel):
    strategy: WindowStrategy = WindowStrategy.SLIDING
    max_tokens: int = 4000
    keep_last_turns: int = 12
    reserve_for_response: int = 800
    pin_system_prompt: bool = True

    @field_validator("strategy", mode="before")
    @classmethod
    def _coerce_strategy(cls, v: Any) -> Any:
        if isinstance(v, str):
            return WindowStrategy(v)
        return v


class TokenConfig(BaseModel):
    backend: str = "heuristic"
    tiktoken_encoding: str = "cl100k_base"
    chars_per_token: float = 4.0


class LLMSummaryConfig(BaseModel):
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"
    endpoint: str = "https://api.openai.com/v1/chat/completions"
    temperature: float = 0.2


class SummaryConfig(BaseModel):
    backend: SummarizerBackend = SummarizerBackend.EXTRACTIVE
    trigger_when_tokens_over: int = 3000
    max_summary_tokens: int = 400
    min_messages_to_summarize: int = 4
    llm: LLMSummaryConfig = Field(default_factory=LLMSummaryConfig)

    @field_validator("backend", mode="before")
    @classmethod
    def _coerce_backend(cls, v: Any) -> Any:
        if isinstance(v, str):
            return SummarizerBackend(v)
        return v


class VectorConfig(BaseModel):
    enabled: bool = True
    backend: EmbeddingBackend = EmbeddingBackend.HASH
    dim: int = 128
    top_k: int = 4
    min_similarity: float = 0.0
    model_name: str = "all-MiniLM-L6-v2"

    @field_validator("backend", mode="before")
    @classmethod
    def _coerce_backend(cls, v: Any) -> Any:
        if isinstance(v, str):
            return EmbeddingBackend(v)
        return v


class PersistenceConfig(BaseModel):
    enabled: bool = True
    sqlite_path: str = ":memory:"
    auto_commit: bool = True
    save_long_term_on_add: bool = True


class SessionConfig(BaseModel):
    default_id: str = "default"
    clear_on_start: bool = False


class MemorySettings(BaseModel):
    """Top-level settings object."""

    window: WindowConfig = Field(default_factory=WindowConfig)
    tokens: TokenConfig = Field(default_factory=TokenConfig)
    summary: SummaryConfig = Field(default_factory=SummaryConfig)
    vector: VectorConfig = Field(default_factory=VectorConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "MemorySettings":
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemorySettings":
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


_DEFAULT_PATH = Path(__file__).with_name("defaults.yaml")


def load_settings(overrides: Optional[dict[str, Any]] = None) -> MemorySettings:
    """Load defaults from defaults.yaml and apply overrides (deep-merged)."""
    with _DEFAULT_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if overrides:
        data = _deep_merge(data, overrides)
    return MemorySettings.from_dict(data)


def _deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge dict b into dict a (b wins on conflicts). Returns a new dict."""
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

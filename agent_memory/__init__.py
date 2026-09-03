"""agent_memory: a modular, configurable memory system for LLM agents.

Top-level export. The public API is intentionally small; users should
mostly interact with `AgentMemory`.
"""
from .agent_memory import AgentMemory
from .config.settings import (
    MemorySettings,
    load_settings,
)
from .core.models import (
    MemoryEntry,
    MemoryPack,
    MemoryQuery,
    Message,
)
from .core.types import (
    EmbeddingBackend,
    MemoryKind,
    Role,
    SummarizerBackend,
    WindowStrategy,
)
from .persistence.store import MemoryStore
from .summary.summarizer import (
    ExtractiveSummarizer,
    ResilientSummarizer,
    Summarizer,
)
from .vector.memory import VectorMemory
from .window.token_counter import (
    HeuristicTokenCounter,
    TokenCounter,
)
from .window.window_manager import WindowManager

__all__ = [
    "AgentMemory",
    "EmbeddingBackend",
    "ExtractiveSummarizer",
    "HeuristicTokenCounter",
    "MemoryEntry",
    "MemoryKind",
    "MemoryPack",
    "MemoryQuery",
    "MemorySettings",
    "MemoryStore",
    "Message",
    "ResilientSummarizer",
    "Role",
    "Summarizer",
    "SummarizerBackend",
    "TokenCounter",
    "VectorMemory",
    "WindowManager",
    "WindowStrategy",
    "load_settings",
]

__version__ = "0.1.0"

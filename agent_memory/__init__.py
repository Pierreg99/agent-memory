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

__all__ = [  # noqa: RUF022
    # Top-level
    "AgentMemory",
    "MemorySettings",
    "load_settings",
    # Models
    "Message",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryPack",
    # Types
    "Role",
    "MemoryKind",
    "WindowStrategy",
    "SummarizerBackend",
    "EmbeddingBackend",
    # Components
    "WindowManager",
    "HeuristicTokenCounter",
    "TokenCounter",
    "Summarizer",
    "ExtractiveSummarizer",
    "ResilientSummarizer",
    "VectorMemory",
    "MemoryStore",
]

__version__ = "0.1.1"

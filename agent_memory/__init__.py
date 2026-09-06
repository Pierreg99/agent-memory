"""agent_memory: a modular, configurable memory system for LLM agents."""
from .agent_memory import AgentMemory
from .config.settings import MemorySettings, load_settings
from .core.models import MemoryEntry, MemoryPack, MemoryQuery, Message
from .core.types import EmbeddingBackend, MemoryKind, Role, SummarizerBackend, WindowStrategy
from .persistence.store import MemoryStore
from .summary.summarizer import ExtractiveSummarizer, ResilientSummarizer, Summarizer
from .vector.memory import VectorMemory
from .window.token_counter import HeuristicTokenCounter, TokenCounter
from .window.window_manager import WindowManager

__all__ = [
    "AgentMemory",
    "MemorySettings",
    "load_settings",
    "Message",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryPack",
    "Role",
    "MemoryKind",
    "WindowStrategy",
    "SummarizerBackend",
    "EmbeddingBackend",
    "WindowManager",
    "HeuristicTokenCounter",
    "TokenCounter",
    "Summarizer",
    "ExtractiveSummarizer",
    "ResilientSummarizer",
    "VectorMemory",
    "MemoryStore",
]

__version__ = "0.2.0"

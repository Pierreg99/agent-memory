"""Context window manager.

The window manager turns a (possibly long) list of messages into the subset
that fits within a token budget, using one of three strategies:

* sliding          - keep the last N turns, drop the rest.
* truncate_oldest  - same, but drop aggressively by oldest-first.
* summarize_old    - delegate the older half to the summarizer.

The manager is intentionally side-effect free: it just returns the messages
that should remain in the prompt. The orchestrator decides what to do with
the dropped messages (e.g. persist them, store a summary, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config.settings import WindowConfig
from ..core.models import Message
from ..core.types import Role, WindowStrategy
from .token_counter import TokenCounter, build_counter


@dataclass
class WindowResult:
    """The output of a windowing operation."""

    kept: list[Message]               # Messages that stay in the context
    dropped: list[Message]            # Messages evicted from the context
    used_tokens: int                  # Tokens used by `kept`
    budget_tokens: int                # Effective budget (= max_tokens - reserve)


class WindowManager:
    """Stateless context window manager."""

    def __init__(
        self,
        config: WindowConfig,
        counter: Optional[TokenCounter] = None,
    ) -> None:
        self.config = config
        self.counter = counter or build_counter()

    @property
    def budget(self) -> int:
        """Effective token budget for the prompt side."""
        return max(1, int(self.config.max_tokens - self.config.reserve_for_response))

    def apply(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
    ) -> WindowResult:
        """Apply the configured strategy and return the windowed result."""
        if not messages:
            return WindowResult(kept=[], dropped=[], used_tokens=0, budget_tokens=self.budget)

        # Count tokens for system prompt (does not evict it)
        sys_tokens = self.counter.count_text(system_prompt) if system_prompt else 0
        budget = max(1, self.budget - sys_tokens)

        strategy = self.config.strategy
        if strategy == WindowStrategy.SLIDING:
            return self._sliding(messages, budget)
        if strategy == WindowStrategy.TRUNCATE_OLDEST:
            return self._truncate_oldest(messages, budget)
        if strategy == WindowStrategy.SUMMARIZE_OLD:
            return self._sliding(messages, budget)  # orchestrator handles summary
        # Default fallback
        return self._sliding(messages, budget)

    # ---- strategies -------------------------------------------------------

    def _sliding(self, messages: list[Message], budget: int) -> WindowResult:
        """Keep as many recent messages as fit, plus the minimum-keep floor."""
        kept: list[Message] = []
        used = 0
        # Walk from newest to oldest
        for m in reversed(messages):
            tc = self.counter.count_messages([m])
            if used + tc <= budget:
                kept.append(m)
                used += tc
            elif len(kept) < self.config.keep_last_turns:
                # Reserve room to satisfy the keep_last_turns floor by
                # precomputing the remaining budget.
                remaining_budget = budget - used
                if tc <= remaining_budget or not kept:
                    kept.append(m)
                    used += tc
            else:
                break
        kept.reverse()
        dropped = [m for m in messages if m not in kept]
        return WindowResult(kept=kept, dropped=dropped, used_tokens=used, budget_tokens=budget)

    def _truncate_oldest(self, messages: list[Message], budget: int) -> WindowResult:
        """Same as sliding but does not protect any minimum floor."""
        kept: list[Message] = []
        used = 0
        for m in reversed(messages):
            tc = self.counter.count_messages([m])
            if used + tc > budget:
                break
            kept.append(m)
            used += tc
        kept.reverse()
        dropped = [m for m in messages if m not in kept]
        return WindowResult(kept=kept, dropped=dropped, used_tokens=used, budget_tokens=budget)

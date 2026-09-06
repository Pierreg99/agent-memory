"""Context window manager."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config.settings import WindowConfig
from ..core.models import Message
from ..core.types import Role, WindowStrategy
from .token_counter import TokenCounter, build_counter


@dataclass
class WindowResult:
    kept: list[Message]
    dropped: list[Message]
    used_tokens: int
    budget_tokens: int


class WindowManager:
    """Stateless context window manager with a strict hard ceiling."""

    def __init__(self, config: WindowConfig, counter: Optional[TokenCounter] = None) -> None:
        self.config = config
        self.counter = counter or build_counter()

    @property
    def budget(self) -> int:
        return max(1, int(self.config.max_tokens - self.config.reserve_for_response))

    def apply(self, messages: list[Message], system_prompt: Optional[str] = None) -> WindowResult:
        if not messages:
            return WindowResult(kept=[], dropped=[], used_tokens=0, budget_tokens=self.budget)

        sys_tokens = self.counter.count_text(system_prompt) if system_prompt else 0
        budget = max(0, self.budget - sys_tokens)
        if budget == 0:
            return WindowResult(
                kept=[],
                dropped=list(messages),
                used_tokens=0,
                budget_tokens=budget,
            )

        if self.config.strategy == WindowStrategy.TRUNCATE_OLDEST:
            return self._truncate_oldest(messages, budget)
        return self._sliding(messages, budget)

    def _sliding(self, messages: list[Message], budget: int) -> WindowResult:
        """Keep the newest messages that fit, never exceeding `budget`.

        `keep_last_turns` is treated as a preference rather than permission
        to violate the hard token ceiling.
        """
        kept: list[Message] = []
        used = 0
        for message in reversed(messages):
            token_count = self.counter.count_messages([message])
            if used + token_count > budget:
                continue
            kept.append(message)
            used += token_count
            if len(kept) >= self.config.keep_last_turns:
                # Continue only when another message also fits; this maximizes
                # context while respecting the hard ceiling.
                continue
        kept.reverse()
        kept_ids = {m.id for m in kept}
        dropped = [m for m in messages if m.id not in kept_ids]
        return WindowResult(kept=kept, dropped=dropped, used_tokens=used, budget_tokens=budget)

    def _truncate_oldest(self, messages: list[Message], budget: int) -> WindowResult:
        kept: list[Message] = []
        used = 0
        for message in reversed(messages):
            token_count = self.counter.count_messages([message])
            if used + token_count > budget:
                continue
            kept.append(message)
            used += token_count
        kept.reverse()
        kept_ids = {m.id for m in kept}
        dropped = [m for m in messages if m.id not in kept_ids]
        return WindowResult(kept=kept, dropped=dropped, used_tokens=used, budget_tokens=budget)

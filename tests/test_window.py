"""Tests for the window manager."""
from agent_memory.config.settings import TokenConfig, WindowConfig
from agent_memory.core.models import Message
from agent_memory.core.types import Role, WindowStrategy
from agent_memory.window.token_counter import HeuristicTokenCounter
from agent_memory.window.window_manager import WindowManager


def _msgs(n: int, content_len: int = 20) -> list[Message]:
    """Build n messages of fixed content length."""
    return [
        Message(role=Role.USER if i % 2 == 0 else Role.ASSISTANT, content="x" * content_len)
        for i in range(n)
    ]


def test_window_empty_input():
    wm = WindowManager(WindowConfig(max_tokens=100, keep_last_turns=2, reserve_for_response=0))
    r = wm.apply([])
    assert r.kept == []
    assert r.dropped == []
    assert r.used_tokens == 0


def test_window_sliding_drops_oldest():
    wm = WindowManager(
        WindowConfig(
            strategy=WindowStrategy.SLIDING,
            max_tokens=200,
            keep_last_turns=2,
            reserve_for_response=0,
        ),
        counter=HeuristicTokenCounter(TokenConfig(chars_per_token=4)),
    )
    # Each message is 20 chars => 5 tokens text + 3 overhead = 8 tokens
    msgs = _msgs(20)
    r = wm.apply(msgs)
    # Budget is 200, so we can fit at most 25 messages; we only have 20
    assert len(r.kept) == 20
    assert r.dropped == []


def test_window_sliding_evicts_when_over_budget():
    wm = WindowManager(
        WindowConfig(
            strategy=WindowStrategy.SLIDING,
            max_tokens=50,
            keep_last_turns=2,
            reserve_for_response=0,
        ),
        counter=HeuristicTokenCounter(TokenConfig(chars_per_token=4)),
    )
    msgs = _msgs(20)  # 8 tokens each => 160 total
    r = wm.apply(msgs)
    # We should only keep messages that fit, but at least keep_last_turns=2
    assert len(r.kept) >= 2
    assert len(r.kept) < 20
    # The most recent message should always be the last input message
    assert r.kept[-1].content == msgs[-1].content


def test_window_reserves_response_tokens():
    wm = WindowManager(
        WindowConfig(max_tokens=200, keep_last_turns=2, reserve_for_response=100),
        counter=HeuristicTokenCounter(TokenConfig(chars_per_token=4)),
    )
    msgs = _msgs(20)
    r = wm.apply(msgs)
    # Effective budget is 100; 100 / 8 = 12 messages
    assert r.budget_tokens == 100
    assert len(r.kept) <= 13  # 12 + slight rounding


def test_window_truncate_oldest_strict():
    wm = WindowManager(
        WindowConfig(
            strategy=WindowStrategy.TRUNCATE_OLDEST,
            max_tokens=30,
            keep_last_turns=10,  # intentionally larger than what fits
            reserve_for_response=0,
        ),
        counter=HeuristicTokenCounter(TokenConfig(chars_per_token=4)),
    )
    msgs = _msgs(20)
    r = wm.apply(msgs)
    # Budget 30 / 8 = 3 messages (with the keep_last_turns floor NOT enforced)
    assert len(r.kept) <= 4


def test_window_accounts_for_system_prompt():
    wm = WindowManager(
        WindowConfig(max_tokens=50, keep_last_turns=1, reserve_for_response=0),
        counter=HeuristicTokenCounter(TokenConfig(chars_per_token=4)),
    )
    msgs = _msgs(5)  # 8 tokens each
    r = wm.apply(msgs, system_prompt="x" * 100)  # 25 tokens
    # Effective budget is 50 - 25 = 25 tokens; only 3 messages fit
    assert r.budget_tokens == 25
    assert len(r.kept) <= 4


def test_window_sliding_keep_last_turns_floor():
    wm = WindowManager(
        WindowConfig(
            strategy=WindowStrategy.SLIDING,
            max_tokens=10,
            keep_last_turns=4,
            reserve_for_response=0,
        ),
        counter=HeuristicTokenCounter(TokenConfig(chars_per_token=4)),
    )
    msgs = _msgs(10)  # each 8 tokens
    r = wm.apply(msgs)
    # Budget is 10 tokens (fits 1 msg), but keep_last_turns floor is 4
    assert len(r.kept) == 4

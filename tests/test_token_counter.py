"""Tests for the token counter."""
from agent_memory.config.settings import TokenConfig
from agent_memory.core.models import Message
from agent_memory.core.types import Role
from agent_memory.window.token_counter import HeuristicTokenCounter, build_counter


def test_heuristic_counts_empty_string():
    c = HeuristicTokenCounter(TokenConfig())
    assert c.count_text("") == 0


def test_heuristic_counts_simple_text():
    c = HeuristicTokenCounter(TokenConfig(chars_per_token=4))
    # 12 chars / 4 chars-per-token = 3 tokens
    assert c.count_text("hello world") == 3


def test_heuristic_counts_nonempty_minimum_one():
    c = HeuristicTokenCounter(TokenConfig(chars_per_token=100))
    assert c.count_text("hi") == 1


def test_heuristic_counts_messages_with_overhead():
    c = HeuristicTokenCounter(TokenConfig(chars_per_token=4))
    msgs = [Message(role=Role.USER, content="hello world")]  # 11 chars
    n = c.count_messages(msgs)
    # 11/4 = 3 text tokens + 3 overhead = 6
    assert n == 6
    # And the message should have been annotated
    assert msgs[0].token_count == 6


def test_heuristic_caches_token_count():
    c = HeuristicTokenCounter(TokenConfig(chars_per_token=4))
    m = Message(role=Role.USER, content="hello", token_count=999)
    assert c.count_messages([m]) == 999


def test_build_counter_returns_heuristic_by_default():
    c = build_counter(TokenConfig(backend="heuristic"))
    assert isinstance(c, HeuristicTokenCounter)

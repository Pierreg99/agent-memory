"""End-to-end demo of the agent memory system.

Run with:
    PYTHONPATH=code python code/examples/run_demo.py

It simulates a multi-turn conversation that:
  1. Stores short-term turns in the persistent message log.
  2. Stores long-term facts (user name, preferences) for RAG retrieval.
  3. Triggers summarization when the conversation grows past the budget.
  4. Returns a `MemoryPack` you can hand to any chat-completions API.

No external API is called - the LLM "reply" is stubbed.
"""
from __future__ import annotations

import os
import sys

# Allow running as a script without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_memory import AgentMemory


def stub_llm(pack) -> str:
    """A fake LLM client that returns a deterministic reply."""
    last_user = next(
        (m.content for m in reversed(pack.recent_messages) if m.role.value == "user"),
        "",
    )
    facts = ", ".join(f.content for f in pack.retrieved_facts) or "no known facts"
    return f"[stub-reply] You said: '{last_user}'. I recall: {facts}"


def main() -> None:
    # 1. Build an AgentMemory with a TINY token budget so we trigger
    #    summarization quickly. In production you would set max_tokens to
    #    match your model's context window.
    mem = AgentMemory.from_config(
        {
            "window": {
                "strategy": "summarize_old",
                "max_tokens": 120,
                "keep_last_turns": 2,
                "reserve_for_response": 30,
            },
            "summary": {
                "trigger_when_tokens_over": 60,
                "max_summary_tokens": 40,
                "min_messages_to_summarize": 3,
            },
            "vector": {"enabled": True, "dim": 64, "top_k": 3},
            "persistence": {"sqlite_path": ":memory:"},
        }
    )

    # 2. Seed long-term facts (RAG memory)
    mem.add_long_term("User's name is Alice", importance=0.95)
    mem.add_long_term("User enjoys hiking in the Alps", importance=0.8)
    mem.add_long_term("User is allergic to peanuts", importance=0.9)

    # 3. Simulate a multi-turn conversation
    turns = [
        ("user", "Hi! I'm new here."),
        ("assistant", "Hello! Welcome, what can I do for you?"),
        ("user", "Can you suggest a weekend trip?"),
        ("assistant", "How about hiking in the mountains?"),
        ("user", "I love hiking in the Alps actually."),
        ("assistant", "Great, the Alps are wonderful in autumn!"),
        ("user", "By the way, what's my name?"),
    ]
    for role, content in turns:
        if role == "user":
            mem.add_user(content)
        else:
            mem.add_assistant(content)

    # 4. Build the LLM-ready context pack
    pack = mem.prepare(
        "What's my name and what do I like?",
        system_prompt="You are a friendly, concise assistant.",
    )

    # 5. Show what the LLM would see
    print("=" * 70)
    print("MEMORY PACK (what the LLM receives)")
    print("=" * 70)
    print(f"Session:           {pack.session_id}")
    print(f"Used / budget:     {pack.used_tokens} / {pack.budget_tokens} tokens")
    print(f"Recent messages:   {len(pack.recent_messages)}")
    print(f"Has summary:       {bool(pack.summary)}")
    print(f"Retrieved facts:   {len(pack.retrieved_facts)}")
    print()
    print("--- Chat messages (verbatim) ---")
    for i, cm in enumerate(pack.to_chat_messages()):
        snippet = cm["content"][:120] + ("..." if len(cm["content"]) > 120 else "")
        print(f"  [{i}] {cm['role']:>9}: {snippet}")
    print()

    # 6. Hand to the LLM (here, a stub)
    print("--- LLM reply ---")
    print(stub_llm(pack))
    print()

    # 7. Close the loop: persist the assistant reply
    mem.add_assistant("Your name is Alice and you love hiking in the Alps!")
    print("--- Stats after turn ---")
    print(mem.stats())


if __name__ == "__main__":
    main()

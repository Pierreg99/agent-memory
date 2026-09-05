# Cookbook

Practical recipes for wiring Agent Memory into an agent loop.

## Minimal chat loop

```python
from agent_memory import AgentMemory

mem = AgentMemory.from_config({
    "persistence": {"sqlite_path": "./chat.db"},
    "window": {"max_tokens": 6000, "reserve_for_response": 800},
})

SYSTEM = "You are a concise assistant."

def turn(user_text: str, llm_call) -> str:
    mem.add_user(user_text)
    pack = mem.prepare(user_text, system_prompt=SYSTEM)
    reply = llm_call(pack.to_chat_messages())
    mem.add_assistant(reply)
    return reply
```

`llm_call` is any function that accepts an OpenAI-style messages list and
returns the assistant text.

## Persist profile facts for RAG

```python
mem.add_long_term("User's name is Alice", importance=0.95, metadata={"source": "profile"})
mem.add_long_term("User is allergic to peanuts", importance=0.9, metadata={"source": "profile"})
mem.add_many_long_term(
    ["Prefers metric units", "Timezone: Europe/Berlin"],
    importance=0.6,
)
```

Query-time overlap matters for the default hash embedder — include key
nouns from the user’s question in the fact text when possible.

## Trigger summarization on long sessions

```python
mem = AgentMemory.from_config({
    "window": {
        "strategy": "summarize_old",
        "max_tokens": 4000,
        "keep_last_turns": 8,
        "reserve_for_response": 800,
    },
    "summary": {
        "backend": "extractive",  # or "llm" with OPENAI_API_KEY set
        "trigger_when_tokens_over": 2800,
        "max_summary_tokens": 400,
        "min_messages_to_summarize": 6,
    },
})
```

Inspect whether a summary fired:

```python
pack = mem.prepare("continue", system_prompt=SYSTEM)
print(bool(pack.summary), pack.used_tokens, pack.budget_tokens)
```

## Exact token accounting with tiktoken

```bash
pip install "agent-memory[tiktoken]"
```

```python
mem = AgentMemory.from_config({
    "tokens": {"backend": "tiktoken", "tiktoken_encoding": "cl100k_base"},
})
```

If tiktoken is not installed, building the counter raises `ImportError`
with an install hint.

## Semantic retrieval with sentence-transformers

```bash
pip install "agent-memory[sentence-transformers]"
```

```python
mem = AgentMemory.from_config({
    "vector": {
        "backend": "sentence_transformers",
        "model_name": "all-MiniLM-L6-v2",
        "top_k": 5,
        "min_similarity": 0.15,
    },
})
```

## Multi-session agents

```python
mem.add_user("hello", session_id="alice")
mem.add_user("bonjour", session_id="bob")
mem.add_long_term("Alice prefers tea", session_id="alice")
mem.add_long_term("Bob prefers coffee", session_id="bob")

pack_a = mem.prepare("drink preference", session_id="alice")
pack_b = mem.prepare("drink preference", session_id="bob")

mem.clear_session("alice")  # bob's store + vector entries remain
```

## Load config from the environment

```bash
export MEMORY_CONFIG_PATH=/etc/agent-memory/prod.yaml
```

```python
mem = AgentMemory.from_config({"vector": {"top_k": 8}})  # dict still wins
```

## Inspect health

```python
print(mem.stats())
# {
#   "session_id": "default",
#   "message_count": ...,
#   "long_term_count": ...,
#   "vector_count": ...,
#   "total_tokens": ...,
#   "budget_tokens": ...,
# }
```

`vector_count` is the in-process vector store length (all sessions).

## Runnable demo

```bash
PYTHONPATH=. python examples/run_demo.py
```

Uses intentionally tiny budgets so summarization and retrieval fire in a
short script without calling a live LLM.

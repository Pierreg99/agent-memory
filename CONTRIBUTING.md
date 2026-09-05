# Contributing

Thanks for helping improve Agent Memory. Keep changes focused, tested,
and documented.

## Setup

```bash
git clone https://github.com/Pierreg99/agent-memory.git
cd agent-memory
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional extras for local experiments:

```bash
pip install -e ".[tiktoken]"
pip install -e ".[sentence-transformers]"
```

## Tests

```bash
python -m pytest tests/ -v
PYTHONPATH=. python examples/run_demo.py
```

Add or update tests for any behavioral change. Prefer small, deterministic
cases (hash embeddings, extractive summarizer, `:memory:` or temp-file
SQLite). Do not commit secrets, API keys, or live network calls in tests.

## Style

- Target Python 3.10+.
- Public APIs should carry concise docstrings and raise explicit errors
  (`ValueError`, `FileNotFoundError`, `RuntimeError`) rather than failing
  silently.
- Keep the default dependency set small; optional backends stay behind
  extras and lazy imports.
- Documentation lives under `docs/` and should stay in sync with code —
  update README links and `CHANGELOG.md` when user-facing behavior changes.

## Pull requests

1. Branch from `main` with a descriptive name (`fix/…`, `docs/…`, `quality/…`).
2. Keep commits readable; one logical change per commit when practical.
3. Ensure CI would pass locally (pytest + demo).
4. Describe findings and trade-offs in the PR body — what was broken or
   missing, what you changed, and how you verified it.

## Security

- Never commit credentials. LLM summarization must read keys from
  environment variables named in config (`api_key_env`), not from source.
- Avoid logging full prompts that may contain user PII in library code.

## License

By contributing you agree that your work is released under the MIT
License (see `LICENSE`).

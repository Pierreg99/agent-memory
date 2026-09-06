# Security & Privacy Review — Agent Memory

## Scope

Review of memory persistence, retrieval isolation, configuration, external LLM calls, and deletion behavior.

## Findings

### High priority

**Persisted memory may contain sensitive data.** SQLite stores message content and long-term facts as plaintext application data. The project currently does not provide encryption, retention enforcement, PII redaction, or access-control hooks.

**External summarization is an explicit data egress path.** The LLM summarizer sends conversation text to a configurable OpenAI-compatible endpoint. Production deployments must treat the endpoint and provider as a data-processing boundary.

**Vector memory is session-filtered but process-local.** Query filtering by `session_id` exists, which is useful for logical isolation, but authorization is outside the library. Callers must not rely on the session ID alone as a security boundary.

### Medium priority

- No built-in audit events for reads, writes, deletions, and exports.
- Metadata is JSON-serialized without a schema or classification model.
- No secret-redaction hook before persistence or external summarization.
- File-backed SQLite path permissions and backup handling are deployment concerns and are not enforced by the library.

## Recommended controls

1. Add an optional `MemoryPolicy` with `allow_external_llm`, retention, maximum content size, metadata classification, and deletion rules.
2. Add provider-neutral `before_store`, `before_summarize`, and `before_retrieve` hooks for redaction and policy enforcement.
3. Add authenticated tenant/session context to storage adapters rather than treating caller-supplied IDs as authorization.
4. Add verifiable delete operations and tests that query every storage/index layer after deletion.
5. Document encryption at rest, backup protection, file permissions, and key-management expectations.
6. Add an audit/telemetry interface for security-relevant operations without storing raw content by default.

## Data-minimization principles

- Store only memory that has a defined retention purpose.
- Prefer structured facts over unrestricted transcript retention when appropriate.
- Separate operational metadata from user content.
- Keep external summarization disabled by default in privacy-sensitive deployments.
- Expose a clear user-driven forget/export path.

## Security test cases

- Cross-session retrieval must always return zero unauthorized entries.
- Deleting a session must remove messages, summaries, long-term facts, and vectors.
- External summarization must not run when policy disallows egress.
- Redaction hooks must run before persistence and before provider calls.
- Oversized content must be rejected or bounded according to policy.

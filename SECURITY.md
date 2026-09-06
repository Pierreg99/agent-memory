# Security & Privacy

## Scope

`agent-memory` is a local memory library. Applications can persist conversation
content, summaries, metadata, and semantic embeddings. Treat the configured
SQLite file and exported session payloads as sensitive data.

## Recommendations

- Use a dedicated filesystem path with operating-system access controls for
  file-backed SQLite databases.
- Do not commit SQLite databases, exported memory JSON, API keys, or model
  credentials to source control.
- Prefer environment variables or a secret manager for LLM credentials.
- Use HTTPS endpoints for hosted summarization services and verify that the
  configured endpoint is an expected provider before deploying untrusted config.
- Scope memory by `session_id` and treat session IDs as authorization boundaries;
  application code remains responsible for authenticating callers.
- Use `clear_session()` for user-requested deletion and `purge_expired()` for
  retention enforcement.
- Review `metadata` carefully: metadata is persisted and exported unchanged.
- Prefer exact token counting (`tiktoken`) when prompt budget compliance is
  critical for a specific model family.

## Data lifecycle

The persistence layer supports explicit session clearing, JSON-serializable
session export, and timestamp-based purge across messages, summaries,
long-term facts, and persisted vectors.

## Retrieval isolation

Vector queries are session-scoped by default through `AgentMemory.prepare()`.
For multi-tenant deployments, maintain a stronger application-level tenant
identifier and enforce it before constructing memory queries.

## Threat model notes

The library is not an authorization system, encrypted database, or DLP engine.
It does not inspect the semantic meaning of text before storing it. Production
applications should add encryption at rest, authentication/authorization,
audit logging, and provider-specific data retention controls when required.

## Reporting

For suspected vulnerabilities, avoid publishing sensitive reproduction data in
public issues. Report the issue privately through the repository's available
security-reporting channel.

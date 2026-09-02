# Project Roadmap

This roadmap outlines the future direction and planned features for `agent-memory`.

## Near-Term (v0.2.0)

- **Vector Database Integrations**:
  - Add optional backend adapters for external vector stores (e.g., Qdrant, ChromaDB, FAISS).
- **Asynchronous API**:
  - Introduce async methods (`add_async`, `prepare_async`) for high-concurrency agent frameworks (FastAPI, asyncio).
- **Expanded Tokenizers**:
  - Add native support for Anthropic and Hugging Face tokenizers.

## Medium-Term (v0.3.0)

- **Memory Decay & Consolidation**:
  - Implement recency-weighted importance decay algorithms.
  - Periodic background consolidation of related memories to optimize retrieval quality.
- **Hierarchical Summarization**:
  - Support multi-level tree summarization for ultra-long multi-session conversations.
- **Enhanced Filtering & Graph RAG**:
  - Graph-assisted memory association and structural relationship queries.

## Long-Term (v1.0.0+)

- **Distributed Persistence & Sync**:
  - Remote storage backends (PostgreSQL / pgvector, Redis, DynamoDB).
  - Multi-tenant memory management with session sync across processes.
- **Telemetry & Evaluation Tools**:
  - Built-in metrics for memory retrieval precision, context compression ratio, and latency benchmarking.

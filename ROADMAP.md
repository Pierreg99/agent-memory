# Agent Memory Roadmap

This roadmap outlines the planned future directions, features, and improvements for `agent-memory`.

## Short-Term Goals (v0.2.0)

- **Vector Database Integration**:
  - Add pluggable store adapters for external vector databases (e.g. ChromaDB, Qdrant, Pinecone, FAISS).
- **Asynchronous API Support**:
  - Provide an `AsyncAgentMemory` orchestrator and async SQLite / store backends for high-concurrency agent runtimes.
- **Tool / Function Calling Memory Support**:
  - Enhanced representation and indexing for tool calls, function executions, and structured tool outputs within conversation context.

## Mid-Term Goals (v0.3.0)

- **Advanced Summarization Strategies**:
  - Incremental tree-of-summaries / hierarchical memory compaction.
  - Multi-session topic extraction and user preference discovery.
- **Enhanced Tokenization**:
  - Support for custom tokenizers (HuggingFace `tokenizers`, Anthropic Count Tokens API integration).
- **Memory Decay and Importance Scoring**:
  - Automatic memory decay mechanisms based on time and relevance feedback.
  - Dynamic importance re-weighting during vector query retrieval.

## Long-Term Vision (v1.0.0)

- **Distributed & Multi-Tenant Persistence**:
  - Production-ready PostgreSQL / Redis storage backends.
  - Multi-tenant tenant isolation and encrypted memory storage.
- **Agent Interoperability**:
  - Out-of-the-box middleware/adapters for popular frameworks (LangChain, LlamaIndex, AutoGen, CrewAI).

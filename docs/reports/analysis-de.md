# Agent Memory — Repository-Analyse (DE)

**Stand:** 2026-09-06
**Repository:** `Pierreg99/agent-memory`
**Branch:** `main`
**Aktueller Release laut Repository:** `0.1.1`

## 1. Executive Summary

`agent-memory` ist eine klar strukturierte Python-Bibliothek für LLM-Agent-Memory. Das Design trennt Orchestrierung, Context-Windowing, Summarization, Long-Term/RAG-Retrieval und SQLite-Persistenz. Die öffentliche API ist klein und die Komponenten sind über Protokolle bzw. injizierbare Abhängigkeiten austauschbar. Das Repository dokumentiert Architektur, API, Konfiguration und Cookbook und besitzt eine CI-Matrix für Python 3.10–3.13.

Die aktuelle Architektur ist sehr geeignet für Prototyping, lokale Agenten und kleinere Deployments. Für produktionskritische oder große Multi-Tenant-Systeme fehlen jedoch zentrale Eigenschaften: persistente Embeddings, robuste Transaktions-/Concurrency-Strategien für hohe Last, differenzierte Daten- und Retention-Policies, Evaluationsmetriken für Retrieval/Summary-Qualität und ein expliziter Security-/Privacy-Lifecycle.

## 2. Architektur-Befund

Der Orchestrator `AgentMemory` lädt Nachrichten, kann bei Überschreiten des Summary-Triggers einen älteren Teil verdichten, führt Windowing aus, ruft Long-Term-Memories ab und liefert einen `MemoryPack`. Diese Pipeline ist im vorhandenen Architecture-Dokument explizit beschrieben.

Stärken:

- Gute Separation of Concerns.
- Klare Pydantic-Modelle an den Systemgrenzen.
- Konfiguration über YAML mit definierter Merge-Priorität.
- Austauschbare Token-Counter, Summarizer, Embeddings und Stores.
- Session-Scope wird beim Vector Retrieval berücksichtigt.

Die Default-Konfiguration ist bewusst leichtgewichtig: heuristischer Token-Counter, Hash-Embeddings, extractive Summary und SQLite. Das reduziert Setup-Kosten, begrenzt aber Genauigkeit und Skalierbarkeit.

## 3. Wichtigste technische Risiken

### 3.1 Embeddings sind nicht persistent

`MemoryStore` persistiert Nachrichten, Summaries und Long-Term-Fakten. Embeddings werden dagegen laut Implementierung nicht in SQLite gespeichert; `VectorMemory` hält Entries und Vektoren ausschließlich in Prozessspeicher. Nach einem Neustart fehlt dadurch der Vector-Index, obwohl die Long-Term-Daten noch vorhanden sind.

**Auswirkung:** persistente RAG-Konfigurationen sind derzeit semantisch unvollständig.

**Priorität: P0/P1**

**Empfehlung:** Embedding-Backend und Vector Store als echte Persistenzschicht definieren. Für kleine Installationen reicht eine SQLite-Tabelle mit Blob/JSON-Embedding; für größere Systeme sind pgvector, Qdrant oder FAISS mit persistenter Indexverwaltung geeigneter.

### 3.2 Heuristischer Token-Counter als Default

Die Standardkonfiguration verwendet `chars_per_token: 4`. Das ist nur eine Näherung und kann insbesondere bei Code, Deutsch, strukturiertem Text und unterschiedlichen Tokenizern von realen Modellbudgets abweichen.

**Auswirkung:** das behauptete Hard Ceiling für den Prompt kann in realen LLM-Aufrufen überschritten werden oder konservativer als nötig ausfallen.

**Empfehlung:** Modell-/Provider-Tokenisierung expliziter machen und den Token-Counter eng an das Zielmodell binden. Der heuristische Counter sollte klar als Fallback gekennzeichnet werden.

### 3.3 Summarization ist inhaltlich nicht ausreichend sprachneutral

Der extractive Summarizer nutzt eine kleine englische Stopword-Liste und einen Regex-Satzsplit, der an Großbuchstaben orientiert ist. Das ist für deutsche, gemischte oder nicht-lateinische Inhalte potenziell schwach.

**Auswirkung:** Qualitätsverlust bei mehrsprachigen Agenten, insbesondere bei langen Konversationen.

**Empfehlung:** sprachunabhängige Sentenz-/Token-Segmentierung und optional modellbasierte Summarization mit Evaluation gegen Recall kritischer Fakten.

### 3.4 Summaries können wiederholt erzeugt werden

`prepare()` persistiert bei Überschreitung des Triggers einen neuen Summary-Eintrag. Es ist keine explizite Dedup-/Coverage-Logik erkennbar, die verhindert, dass dieselben älteren Nachrichten wiederholt in neue Summaries einfließen.

**Auswirkung:** unnötige Summary-Erzeugung und potenziell wachsende Summary-Historie; bei LLM-Backend entstehen zusätzliche Kosten.

**Empfehlung:** Summary-Coverage als monotonen Cursor oder Message-Watermark modellieren und nur neue, noch nicht zusammengefasste Inhalte verdichten.

### 3.5 SQLite-Concurrency ist für hohe Last nur begrenzt ausgelegt

Der Store verwendet Thread-local Connections und `check_same_thread=False`; das ist für Thread-Sicherheit eines einzelnen Connection-Objekts pragmatisch. Das Modell ersetzt jedoch keinen echten Connection-Pool bzw. keine Laststrategie für mehrere Worker-Prozesse. Besonders `:memory:` ist pro Connection isoliert.

**Empfehlung:** dokumentierten Produktionspfad für File-SQLite mit WAL + Busy-Timeout oder externe DB als Referenzarchitektur ergänzen.

## 4. API- und Datenmodell-Bewertung

Die Public API ist kompakt (`add_user`, `add_assistant`, `add_long_term`, `prepare`, `stats`, `clear_session`). `MemoryPack.to_chat_messages()` bietet eine einfache Provider-Schnittstelle.

Positiv:

- IDs, Timestamps, Metadata und Importance sind bereits vorhanden.
- `MemoryQuery` unterstützt Session-, Kind-, Importance- und Metadata-Filter.
- Die Zusammenfassung speichert `source_message_ids`, was Auditierbarkeit ermöglicht.

Verbesserungspotenzial:

- Explizite `MemorySource`/Provenance-Felder.
- Lifecycle-Felder wie `expires_at`, `last_accessed_at`, `access_count`, `confidence`.
- Namespace/Tenant/Agent-ID zusätzlich zu `session_id`.
- Revisions-/Supersedes-Beziehungen für korrigierbare Memories.
- Einheitliche Fehlerklassen statt ausschließlich `ValueError`/`RuntimeError`.

## 5. Retrieval-Design

`VectorMemory.query()` berechnet Cosine Similarity über alle gespeicherten Vektoren; der aktuelle Ansatz ist O(N) und wird in der Implementierung selbst als passend für Tausende Einträge beschrieben.

Das ist als austauschbarer Ausgangspunkt sinnvoll. Für Produktion sollte die Retrieval-Pipeline jedoch erweitert werden um:

1. Hybrid Search (lexikalisch + semantisch).
2. Recency/importance weighting.
3. Reranking.
4. Duplicate/near-duplicate suppression.
5. Retrieval telemetry (score, source, latency, selected/rejected candidates).
6. Persistente Indexierung.

## 6. Security & Privacy

Der API-Key für den LLM-Summarizer wird aus einer Environment Variable gelesen. Das verhindert Secrets im YAML, ist aber nur ein Teil einer vollständigen Security-Story.

Empfohlene Erweiterungen:

- Redaction/PII hooks vor Persistenz und Embedding.
- Verschlüsselungsoption für sensible Stores.
- Explizite Retention- und Delete-Policies.
- Tenant-Isolation und Autorisierung auf Store-/Query-Ebene.
- Audit Events für add/query/delete/summary.
- SSRF-/Endpoint-Allowlisting für konfigurierbare LLM-Endpunkte.
- Größenlimits für Message Content und Metadata.

## 7. Testing & CI

Das Repository enthält Tests für Config, Gaps, Models, Orchestrator, Persistence, Summary, Token Counting, Vector und Windowing. Das README nennt 63 lokal bestandene Tests. CI führt die Suite für Python 3.10–3.13 aus und enthält zusätzlich einen Packaging/Import-Smoke-Test sowie den Demo-Lauf.

Fehlende bzw. ausbaufähige Testklassen:

- Persistenz über Prozess-Neustarts.
- Concurrent writers/readers mit SQLite.
- Property-/Fuzz-Tests für Windowing und Token-Budgets.
- Mehrsprachige Summaries.
- Retrieval-Regression-Sets mit Recall@k / Precision@k.
- Embedding-Dimension- und Backend-Kompatibilität.
- Secret-/Endpoint-Sicherheitsfälle.
- Performance-Benchmarks für N = 1k / 10k / 100k Memories.

## 8. Produktions-Roadmap

### P0 — Correctness & Durability

- Persistente Embeddings oder persistente externe Vector DB.
- Summary-Coverage-Watermark.
- Exakte Tokenizer-Unterstützung pro Modell.
- Persistenz-Regressionstests nach Process Restart.

### P1 — Quality & Scale

- Hybrid Retrieval + Reranking.
- Recency/importance scoring.
- Retrieval and summarization evaluation suite.
- SQLite WAL/timeout tuning bzw. DB abstraction für Postgres.
- Batch-APIs für ingest/embedding.

### P2 — Governance & Observability

- Memory TTL/retention.
- Provenance/confidence.
- PII redaction/encryption hooks.
- Structured telemetry and audit events.
- Tenant/namespace isolation.

### P3 — Ecosystem

- Provider adapters für moderne Chat APIs.
- Standardisierte Store- und Embedder-Interfaces mit Capability Detection.
- Optional async API (`await add`, `await prepare`) für Web Services.
- Migration/versioning utilities für Memory-Schemas.

## 9. Zielarchitektur für `0.2.x`

```text
AgentMemory
   |
   +--> Context Manager
   |      +--> exact Tokenizer
   |      +--> Window Policy
   |      +--> Summary Policy
   |
   +--> Memory Router
   |      +--> Short-term Store
   |      +--> Long-term Store
   |      +--> Vector Index
   |
   +--> Retrieval Pipeline
   |      +--> filters
   |      +--> semantic/lexical search
   |      +--> reranker
   |      +--> recency/importance scoring
   |
   +--> Governance
   |      +--> provenance
   |      +--> retention
   |      +--> redaction
   |      +--> audit
   |
   +--> Observability
          +--> latency
          +--> token usage
          +--> retrieval quality
          +--> summary quality
```

## 10. Gesamturteil

**Architektur: 8/10** — gut modularisiert und verständlich.

**Developer Experience: 8/10** — kleine API, gute Dokumentation und vorhandene Demo/CI.

**Correctness/Durability: 6/10** — Persistenz und Vector-Lifecycle müssen zusammengeführt werden.

**Retrieval Quality: 6/10** — funktional, aber derzeit einfach und O(N).

**Production Readiness: 5/10** — gute Basis, aber Governance, Evaluation, Observability und Skalierung fehlen.

**Empfohlener nächster Schwerpunkt:** persistenter Memory-Lifecycle (Embeddings + Coverage), danach Evaluation und Hybrid Retrieval.

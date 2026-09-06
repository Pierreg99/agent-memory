# Produktions-Roadmap — Agent Memory

## Ziel

Diese Roadmap übersetzt die Repository-Analyse in konkrete, priorisierte Maßnahmen für einen robusteren produktiven Einsatz.

## P0 — zuerst beheben

### 1. Persistenter Vector Index
Die aktuelle `VectorMemory` hält Entries und Embeddings nur in Python-Listen. SQLite persistiert zwar Nachrichten, Summaries und Long-Term-Fakten, aber nicht die Embeddings. Nach einem Prozessneustart ist der semantische Index damit leer.

**Maßnahme:** Embedding-Backend als persistierbare Abstraktion definieren und mindestens einen SQLite-basierten Persistenzmodus implementieren. Für größere Installationen einen Adapter für Qdrant, pgvector oder FAISS mit gespeicherten Index-Metadaten vorsehen.

### 2. Konsistente Summary-Ketten
`prepare()` erzeugt bei Überschreitung des Schwellwerts einen neuen Summary-Eintrag, während alte Summary-Einträge erhalten bleiben. Die Datenstruktur sollte explizit festhalten, welchen Message-Bereich ein Summary abdeckt und welche Summary-Version aktuell ist.

**Maßnahme:** Summary-Coverage als monotone Range/Set-Repräsentation, Versionierung und Idempotenz-Checks einführen.

### 3. Token-Budget als harte Invariante
Der Default ist ein heuristischer Token-Counter. Für Produktionsmodelle sollte vor dem Request eine modellnahe Zählung erfolgen und die resultierende Chat-Payload die Budgetgrenze garantiert einhalten.

**Maßnahme:** `model_name`/Tokenizer-Profil konfigurieren, Preflight-Validation einführen und bei fehlender exakter Tokenizer-Unterstützung explizit als Approximation markieren.

### 4. Memory-Lifecycle und Löschung
Ein produktives Memory-System benötigt explizite Regeln für Retention, Löschung, Korrektur und Export. `clear_session()` ist vorhanden, aber Retention- und Garbage-Collection-Policies fehlen.

**Maßnahme:** TTL/Retention, `forget(entry_id)`, `forget_by_metadata()`, Export/Import und verifizierte Löschung ergänzen.

## P1 — nächster Ausbau

### Retrieval-Qualität
Der aktuelle Vector Store führt lineare Suche über alle In-Memory-Vektoren aus. Das ist für kleine Datenmengen ausreichend, skaliert aber nicht gut.

**Maßnahmen:** Hybrid Retrieval (lexikalisch + semantisch), Recency/importance weighting, Diversity/duplicate suppression und optionales Reranking.

### Mehrsprachige Summaries
Der Extractive-Summarizer verwendet eine kleine englische Stopword-Liste und eine englisch geprägte Satzsegmentierung. Für Deutsch und weitere Sprachen ist die Qualität daher begrenzt.

**Maßnahmen:** Sprachprofile oder sprachunabhängige Provider-Strategie; Tests für Deutsch/Englisch; LLM-Summarization mit strukturierter Ausgabe.

### Observability
Erfassen: Token-Budget-Nutzung, Summary-Triggers, Retrieval-Hit-Rate, Latenz, Fehler/Fallbacks und Memory-Wachstum.

**Maßnahme:** Callback/Telemetry-Interface ohne harte Provider-Abhängigkeit.

### Concurrency
Thread-lokale SQLite-Verbindungen sind vorhanden. Für hochparallele Server fehlen aber klare Transaktions- und Pooling-Regeln.

**Maßnahmen:** Connection lifecycle dokumentieren, WAL-Modus optional aktivieren, Retry/Busy-Timeout und transaktionale Batch-Operationen ergänzen.

## P2 — Reifegrad

- Versioniertes Storage-Schema und Migrationen
- Multi-tenant namespace isolation
- Verschlüsselung sensibler Memory-Daten auf Anwendungsebene
- Secrets-/PII-Redaction hooks
- Memory provenance und source attribution
- Evaluation-Suite gegen reale Konversationen
- Benchmarking für N=1k/10k/100k Entries
- Stable semantic-versioning policy

## Empfohlene Zielarchitektur

```text
AgentMemory
  |
  +-- Context Policy
  |     +-- Tokenizer
  |     +-- Windowing
  |     +-- Summary policy
  |
  +-- Memory Service
  |     +-- Working memory
  |     +-- Long-term memory
  |     +-- Retrieval / reranking
  |     +-- Provenance
  |
  +-- Storage Adapters
  |     +-- SQLite
  |     +-- pgvector/Qdrant/etc.
  |
  +-- Governance
        +-- retention
        +-- deletion
        +-- PII controls
        +-- audit/telemetry
```

## Akzeptanzkriterien für Production

1. Neustart verändert Retrieval-Ergebnisse nicht unerwartet.
2. Kein erzeugtes Prompt überschreitet sein konfiguriertes Token-Budget.
3. Jede Summary ist rückverfolgbar und idempotent.
4. Einzelne Sessions/Tenants können vollständig gelöscht werden.
5. Retrieval kann reproduzierbar evaluiert werden.
6. Fehler des optionalen LLM- oder Embedding-Backends degradieren kontrolliert.

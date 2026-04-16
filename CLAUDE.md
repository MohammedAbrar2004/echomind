# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What is EchoMind?

EchoMind is a single-user personal cognitive memory system. It passively ingests conversational and document data from multiple sources (WhatsApp, Gmail, Google Meet, Google Calendar, manual entry), normalizes everything into a structured knowledge base, and will eventually make it queryable through a conversational interface.

The core idea: you should never lose context on what was said, what was promised, what was scheduled, or what needs to be done — across all your communication channels.

---

## Tech Stack

- **Language:** Python 3.11
- **API Framework:** FastAPI
- **Database:** PostgreSQL 12+ with pgvector
- **WhatsApp Service:** Node.js with Baileys
- **Environment:** Conda (`echomind`)
- **OS:** Windows (local machine)
- **Key Python packages:** psycopg2, pydantic, google-auth, google-api-python-client, APScheduler, python-dotenv

---

## Running the Project

Three processes run concurrently in separate terminals:

```bash
# Terminal 1: FastAPI receiver
python -m uvicorn app.api.receiver:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: WhatsApp Baileys service
cd services/whatsapp && npm start

# Terminal 3: Scheduler for pull-based connectors (Gmail, Calendar, etc.)
python app/schedular/scheduler.py
```

**First-time setup:**
```bash
# Python (activate conda env first: conda activate echomind)
pip install -r requirements.txt

# Node.js
cd services/whatsapp && npm install

# Initialize DB (PostgreSQL + pgvector must already be running)
python app/db/init_db.py
```

---

## Testing

```bash
# Python
pytest tests/ -v
pytest tests/performance/ -v -m performance
pytest tests/ --cov=app --cov-report=html

# JavaScript
npm --prefix tests-js test
npm --prefix tests-js run test:perf
```

---

## System Architecture (Layered)

### Layer 1 — Data Input & Ingestion ✅ Active
Connectors normalize raw source data into `NormalizedInput` (Pydantic model in `models/normalized_input.py`) — the universal contract between connectors and the pipeline. `MediaService` handles all file saving. WhatsApp pushes messages to FastAPI; Gmail and others are pulled by the scheduler.

### Layer 2 — Preprocessing & Raw Persistence ✅ Active
Cleans and normalizes text, scores initial salience, writes to `memory_chunks` and `media_files`. Acts as a safe checkpoint — raw data is preserved before any downstream processing.

### Layer 3 — Semantic Extraction ❌ Not built
Will read `memory_chunks` and extract entities, events, relationships, and refined salience scores into `entities`, `events`, and `entity_event_links` tables.

### Layer 4 — Retrieval Engine ❌ Not built
Will combine pgvector similarity search with structured graph queries and temporal ordering to produce ranked context for the response layer.

### Layer 5 — Response & Agent Layer ❌ Not built
LLM-powered chat/voice UI, automated email drafts, calendar event creation, commitment tracking, and todo list management from detected tasks.

---

## Data Flows

**Push mode (WhatsApp):**
1. Baileys service (`services/whatsapp/`) detects a message → POSTs to `POST /ingest/whatsapp`
2. `app/api/receiver.py` calls `WhatsAppConnector.fetch_from_push()`
3. Connector returns `NormalizedInput` objects (media routed through `MediaService`)
4. `pipelines/ingestion_pipeline.py` → preprocessor → `repository.py` → DB

**Pull mode (Gmail, Calendar, etc.):**
1. `app/schedular/scheduler.py` fires every `SCHEDULER_INTERVAL_MINUTES`
2. `ingestion_pipeline.run_ingestion()` calls each connector's `fetch_data()`
3. Same preprocessor → repository → DB path as push mode

---

## Database

PostgreSQL + pgvector. Key tables:

| Table | Purpose |
|---|---|
| `memory_chunks` | All ingested content; 1536-dim embeddings, salience scores |
| `media_files` | Media file paths/metadata linked to `memory_chunks` |
| `entities` | Extracted people, places, organizations (Layer 3) |
| `events` | Detected meetings, deadlines, commitments (Layer 3) |
| `entity_event_links` | Relationships between entities and events (Layer 3) |
| `data_sources` | Connector registry with ingestion mode (push/pull) |
| `processing_queue` | Async job queue for semantic processing |
| `ingestion_runs` | Audit log per ingestion cycle |
| `failed_jobs` | Retry queue for failed processing |

Deduplication is enforced at DB level via `UNIQUE(source_id, external_message_id)` on `memory_chunks`.

---

## Key File Locations

| Path | Role |
|---|---|
| `models/normalized_input.py` | Universal data contract — all connectors output this |
| `app/api/receiver.py` | FastAPI entry point for push-based ingestion |
| `app/connectors/` | One subfolder per source, each extending `base_connector.py` |
| `app/services/media_service.py` | All media file saving — never save files directly elsewhere |
| `app/preprocessing/preprocessor.py` | Text cleaning and salience scoring |
| `app/db/schema.sql` | Full PostgreSQL schema |
| `app/db/repository.py` | All DB writes — never write raw SQL outside this file |
| `pipelines/ingestion_pipeline.py` | Orchestrates connectors → preprocessing → DB |
| `app/schedular/scheduler.py` | APScheduler background jobs |
| `services/whatsapp/` | Node.js Baileys WhatsApp service |

---

## Environment Variables

Create `.env` in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=echomind
DB_USER=postgres
DB_PASSWORD=postgres123

RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000

WHATSAPP_TARGET_CHATS=["Contact Name"]
WHATSAPP_POLL_INTERVAL_MINUTES=30
WHATSAPP_SESSION_PATH=./services/whatsapp/session

SCHEDULER_INTERVAL_MINUTES=30

OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
GMAIL_API_KEY=your_key
```

---

## Current Development Status

### Complete
- PostgreSQL schema with all tables
- `NormalizedInput` Pydantic model
- `MediaService` — saves media locally, returns `MediaObject`
- `GmailConnector` — OAuth, fetches unread emails + attachments, end-to-end verified
- `ingestion_pipeline.py` + `repository.py` for DB writes
- `preprocessor.py` — text cleaning and salience scoring
- Connector folder structure organized by source

### In Progress
- WhatsApp connector — migrating from `whatsapp-web.js` to Baileys (browser automation was unstable)
- WhatsApp media handling (voice notes, PDFs, Word docs)

### Not Yet Built
- Semantic extraction (Layer 3), vector embeddings, retrieval engine (Layer 4), response/agent layer (Layer 5)
- Calendar, Google Meet, and Manual connectors
- Chat UI / Voice UI

---

## Development Rules

- **Build → Test → Stabilize → Proceed.** No layer starts until the previous one is stable.
- **All DB writes go through `repository.py`** — never raw SQL in connectors or pipeline.
- **All media saves go through `MediaService`** — never write files directly from connectors.
- **Do not suggest `whatsapp-web.js` fixes** — the project is migrating to Baileys.
- **Gmail HTML stripping needs improvement** — the current implementation is incomplete.
- **Preserve what works** — WhatsApp text ingestion and Gmail ingestion are confirmed stable.
- No premature abstraction — implement only what's needed for the current phase.

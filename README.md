# EchoMind - Personal Cognitive Memory System

> A single-user personal cognitive memory system that passively ingests conversational and document data from multiple sources, normalizes everything into a structured knowledge base, and makes it queryable through a conversational interface.

## 🎯 Overview

**The core idea:** You should never lose context on what was said, what was promised, what was scheduled, or what needs to be done — across all your communication channels.

EchoMind connects to:
- **Gmail** - Email messages + attachments
- **Google Calendar** - Upcoming events
- **Google Meet** - Past recordings
- **WhatsApp** - Chat messages (push via Node.js service)
- **Manual Uploads** - Any documents you want to remember

All data flows through a pipeline that:
1. **Fetches** data from multiple sources
2. **Normalizes** everything to a common format
3. **Preprocesses** text and scores importance
4. **Stores** in PostgreSQL with metadata
5. **Tracks** errors and provides detailed logging

---

## 🏗️ Architecture

### Layer 1: Data Input & Ingestion ✅ COMPLETE
- 5 connectors (Gmail, Calendar, GMeet, Manual, WhatsApp)
- Push mode (WhatsApp, Manual) and pull mode (Gmail, Calendar, GMeet)
- Media attachment handling (PDFs, documents, voice notes)
- Error handling with retry logic

### Layer 2: Preprocessing & Persistence ✅ COMPLETE
- Text cleaning and normalization
- Salience scoring (importance estimation)
- Media file management
- Database persistence with deduplication

### Layer 3: Semantic Extraction ❌ FUTURE
- Entity extraction (people, places, organizations)
- Event detection (meetings, deadlines, tasks)
- Refined salience scoring
- Vector embeddings (1536-dim)

### Layer 4: Retrieval Engine ❌ FUTURE
- pgvector similarity search
- Graph-based queries (entity relationships)
- Temporal ordering and ranking

### Layer 5: Response & Agent Layer ❌ FUTURE
- Chat interface
- Automated email drafts
- Calendar event creation
- Commitment tracking

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Required:
- Python 3.11+
- PostgreSQL 12+ (with pgvector extension)
- Node.js 16+ (for WhatsApp service, optional)

# Verify PostgreSQL is running:
psql -U postgres -c "SELECT version();"
```

### 2. Installation

```bash
# Clone and enter directory
cd c:\Users\abrar\Desktop\echomind

# Create and activate conda environment (recommended)
conda create -n echomind python=3.11
conda activate echomind

# Install Python dependencies
pip install -r requirements.txt

# Initialize database (creates tables and extensions)
python app/db/init_db.py
```

### 3. Configuration

Create `.env` file in project root:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=echomind
DB_USER=postgres
DB_PASSWORD=postgres123

# API Receiver (for WhatsApp push)
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000

# Scheduler (for pull-based connectors)
SCHEDULER_INTERVAL_MINUTES=30

# Media
MEDIA_BASE_DIR=./media

# Optional: Google API credentials for Gmail, Calendar, GMeet
# Download from: https://console.cloud.google.com/
# Place credentials.json in: app/connectors/gmail/
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
GMAIL_API_KEY=your_key_here
```

### 4. Run the Project

**Option A: Full Stack (All 3 services)**

Terminal 1 - API Receiver:
```bash
python -m uvicorn app.api.receiver:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 - Scheduler (pull-based connectors):
```bash
python app/schedular/scheduler.py
```

Terminal 3 - WhatsApp Baileys Service (optional):
```bash
cd services/whatsapp
npm install
npm start
```

**Option B: Manual One-Time Ingestion**
```bash
# Run entire pipeline once
python -c "from pipelines.ingestion_pipeline import run_ingestion; import json; print(json.dumps(run_ingestion(), indent=2))"
```

**Option C: Verify Installation**
```bash
# Test all components
python verify_echomind.py
```

### 5. Test Data

Create test files for manual ingestion:
```bash
mkdir -p data/manual_uploads

# Add test files
echo "Meeting notes: Discussed Q1 roadmap and budget allocation" > data/manual_uploads/meeting_notes.txt
echo "Action items: Finalize design by Friday, schedule review" > data/manual_uploads/action_items.txt

# Run ingestion (scheduler will pick these up)
python app/schedular/scheduler.py

# Or manually trigger
python -c "from app.connectors.manual.manual_connector import ManualConnector; print(f'Items found: {len(ManualConnector().fetch_data())}')"
```

---

## 📦 Project Structure

```
echomind/
├── app/
│   ├── api/
│   │   └── receiver.py                 # FastAPI endpoint for WhatsApp push
│   ├── connectors/                     # Data source connectors
│   │   ├── base_connector.py           # Abstract base class
│   │   ├── gmail/
│   │   │   ├── gmail_connector.py      # Email + attachments
│   │   │   ├── credentials.json        # Google OAuth (user-provided)
│   │   │   └── token.json              # Auth token (auto-generated)
│   │   ├── calendar/
│   │   │   └── calendar_connector.py   # Calendar events
│   │   ├── gmeet/
│   │   │   └── gmeet_connector.py      # Meet recordings
│   │   ├── manual/
│   │   │   └── manual_connector.py     # File uploads
│   │   ├── whatsapp/
│   │   │   └── whatsapp_connector.py   # WhatsApp message push
│   │   └── phone/
│   │       └── phone_connector.py      # Phone calls (stub)
│   ├── db/
│   │   ├── connection.py               # PostgreSQL connection
│   │   ├── init_db.py                  # Initialize database schema
│   │   ├── repository.py               # Database write functions
│   │   └── schema.sql                  # SQL schema definition
│   ├── preprocessing/
│   │   └── preprocessor.py             # Text cleaning + salience scoring
│   ├── services/
│   │   └── media_service.py            # File saving and metadata
│   ├── schedular/
│   │   └── scheduler.py                # APScheduler for pull-based sources
│   ├── utils/
│   │   ├── error_handler.py            # Error tracking + retry logic
│   │   └── logger.py                   # Structured logging
│   └── embeddings/                     # Placeholder for Layer 3
├── models/
│   └── normalized_input.py             # Universal data contract (Pydantic)
├── pipelines/
│   └── ingestion_pipeline.py           # Orchestrates connectors → DB
├── services/
│   └── whatsapp/                       # Node.js Baileys service
├── tests/
│   └── integration/
│       └── test_connectors_integration.py  # Comprehensive test suite
├── data/
│   └── manual_uploads/                 # User-uploaded files (scanned by cron)
├── media/
│   ├── images/                         # Uploaded images
│   ├── audio/                          # Voice notes
│   ├── documents/                      # PDFs, Word, Excel
│   └── video/                          # Video files
├── logs/
│   ├── echomind.log                    # All messages
│   └── echomind_errors.log             # Errors/warnings only
├── .env                                # Configuration (user-created)
├── .env.example                        # Config template
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
└── CLAUDE.md                           # Architecture notes
```

---

## 🔌 API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "ok", "service": "EchoMind Receiver"}
```

### WhatsApp Ingestion (Push)
```bash
POST /ingest/whatsapp

Request body:
{
  "messages": [
    {
      "chat_name": "My Friends",
      "message_id": "msg_123",
      "timestamp": "2026-04-16T10:30:00Z",
      "sender": "alice",
      "message": "Let's meet tomorrow",
      "is_group": true,
      "has_media": false
    }
  ]
}

Response:
{
  "status": "ok",
  "received": 1,
  "inserted": 1,
  "duplicates": 0,
  "errors": 0
}
```

---

## 📊 Database Schema

### Key Tables

**memory_chunks** - All ingested content
```sql
SELECT * FROM memory_chunks LIMIT 5;
-- Fields: id, user_id, source_id, external_message_id, timestamp, 
--         content_type, raw_content, embedding, salience_score, metadata
```

**media_files** - Attached files
```sql
SELECT * FROM media_files LIMIT 5;
-- Linked to memory_chunks via FK, tracks original filename, mime type, local path
```

**data_sources** - Connector registry
```sql
SELECT * FROM data_sources;
-- Tracks ingestion mode (push/pull), last sync time
```

**system_logs** - Audit trail
```sql
SELECT * FROM system_logs WHERE created_at > NOW() - INTERVAL '1 day';
```

**failed_jobs** - Retry queue
```sql
SELECT * FROM failed_jobs ORDER BY created_at DESC LIMIT 10;
```

### Check Data
```bash
# Connect to database
psql -h localhost -U postgres -d echomind

# See all memory chunks
SELECT COUNT(*) as total_chunks FROM memory_chunks;
SELECT COUNT(*) as total_media FROM media_files;

# See recent ingestions by source
SELECT source_id, COUNT(*) as count 
FROM memory_chunks 
GROUP BY source_id 
ORDER BY count DESC;

# See ingestion errors
SELECT * FROM system_logs 
WHERE level IN ('WARNING', 'ERROR') 
ORDER BY created_at DESC LIMIT 20;
```

---

## 🧪 Testing

### Run All Tests
```bash
# From project root
pytest tests/integration/ -v

# With detailed output
pytest tests/integration/ -vv -s

# Specific test class
pytest tests/integration/test_connectors_integration.py::TestConnectorIntegration -v

# Specific test
pytest tests/integration/test_connectors_integration.py::TestConnectorIntegration::test_manual_connector -v
```

### Test Coverage

The consolidated test file (`tests/integration/test_connectors_integration.py`) includes:

1. **TestConnectorIntegration** - All 5 data sources
2. **TestMediaHandling** - File saving and tracking
3. **TestErrorHandling** - Error tracking and retries
4. **TestPipelineIntegration** - End-to-end workflows

---

## 🛠️ Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"
if [ $? -ne 0 ]; then
    # Start PostgreSQL (Windows)
    net start PostgreSQL-13  # or your version
fi

# Verify .env file
cat .env | grep DB_

# Check extension
psql -U postgres -d echomind -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
```

### Connector Authentication Failed
```bash
# Gmail/Calendar/GMeet need credentials.json
# Download from: https://console.cloud.google.com/
# 1. Create OAuth 2.0 credentials (Desktop app)
# 2. Download JSON file
# 3. Place in: app/connectors/gmail/credentials.json
# 4. First run will open browser for authorization
```

### No Data Appearing in Database
```bash
# 1. Check if connectors are running
tail -f logs/echomind.log | grep "Connector\|Retrieved"

# 2. Verify manual uploads are in correct directory
ls -la data/manual_uploads/

# 3. Run manual ingestion test
python -c "
from app.connectors.manual.manual_connector import ManualConnector
results = ManualConnector().fetch_data()
print(f'Manual connector: {len(results)} items')
for r in results:
    print(f'  - {r.external_message_id}')
"

# 4. Check database directly
psql -h localhost -U postgres -d echomind -c "SELECT COUNT(*) FROM memory_chunks;"
```

### High CPU/Memory Usage
```bash
# Check what's running
ps aux | grep python

# Scheduler interval too short? Increase in .env
SCHEDULER_INTERVAL_MINUTES=60

# Too many media files? Check disk space
df -h media/

# Archive old logs
mv logs/echomind.log logs/echomind.log.$(date +%Y%m%d).bak
```

### WhatsApp Service Not Receiving Messages
```bash
# Ensure Node.js service is running
cd services/whatsapp
npm start

# Check service logs
tail -f logs/whatsapp.log

# Test endpoint manually
curl -X POST http://127.0.0.1:8000/ingest/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"chat_name": "Test", "message_id": "1", "timestamp": "2026-04-16T00:00:00Z", "sender": "test", "message": "Hello", "is_group": false, "has_media": false}]}'
```

---

## 📝 Common Tasks

### Add Custom File Types to Manual Connector
Edit `app/connectors/manual/manual_connector.py`:

```python
SUPPORTED_ATTACHMENTS = {
    '.custom': 'application/custom-type',
    # Add your MIME types here
}
```

### Change Ingestion Schedule
Edit `.env`:
```env
SCHEDULER_INTERVAL_MINUTES=15  # Default: 30
```

### Increase Logging Detail
Edit `.env` or when running:
```bash
# Set logging level to DEBUG
python app/schedular/scheduler.py --log-level DEBUG
```

### Export Data
```bash
# Dump memory_chunks to CSV
psql -h localhost -U postgres -d echomind -c "\COPY memory_chunks(id, source_id, external_message_id, raw_content, timestamp) TO STDOUT WITH CSV HEADER;" > export_$(date +%Y%m%d).csv

# Dump to JSON
psql -h localhost -U postgres -d echomind -c "SELECT row_to_json(t) FROM memory_chunks t LIMIT 100;" > export_$(date +%Y%m%d).json
```

---

## 🚦 Status & What's Next

### ✅ Complete (Layers 1-2)
- Data input from 5 sources
- Preprocessing and storage
- Error handling and logging
- Media file management
- Integration tests

### ❌ In Development (Layers 3-5)
- Semantic extraction (entities, events)
- Vector embeddings
- Retrieval engine
- LLM agent interface
- Chat UI

### If You Want to Contribute
Layers 3-5 are not started. Good starting points:
1. Implement entity extraction in `app/embeddings/`
2. Add pgvector similarity search
3. Build chat endpoint
4. Create UI (React/Vue/Svelte)

---

## 📋 Configuration Reference

### .env Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| DB_HOST | Yes | localhost | PostgreSQL host |
| DB_PORT | Yes | 5432 | PostgreSQL port |
| DB_NAME | Yes | echomind | Database name |
| DB_USER | Yes | postgres | Database user |
| DB_PASSWORD | Yes | postgres123 | Database password |
| RECEIVER_HOST | No | 127.0.0.1 | API server host |
| RECEIVER_PORT | No | 8000 | API server port |
| SCHEDULER_INTERVAL_MINUTES | No | 30 | Cron interval (minutes) |
| MEDIA_BASE_DIR | No | ./media | Media storage path |
| OPENAI_API_KEY | No | - | For future LLM features |

---

## 🔐 Security Notes

**This is a single-user prototype.** User ID is hardcoded. Before multi-user use:

1. Remove hardcoded USER_ID from `pipelines/ingestion_pipeline.py`
2. Implement user authentication
3. Add row-level security policies
4. Encrypt sensitive data in database
5. Secure credential storage (use AWS Secrets Manager, HashiCorp Vault, etc.)

---

## 📞 Support & FAQ

**Q: Can I use this without Google credentials?**  
A: Yes! Manual uploads and WhatsApp work without any credentials. Gmail/Calendar/GMeet are optional.

**Q: How much data can it handle?**  
A: PostgreSQL can handle millions of records. Media storage depends on your disk. Typical usage: 100-1000 items/month.

**Q: How often should I run ingestion?**  
A: Default every 30 minutes. More frequent = higher API quota usage. Adjust `SCHEDULER_INTERVAL_MINUTES`.

**Q: Is my data private?**  
A: Yes! Everything runs locally on your machine. PostgreSQL and media files are on your disk.

**Q: Can I delete old data?**  
A: Yes. Use SQL:
```sql
DELETE FROM memory_chunks WHERE created_at < NOW() - INTERVAL '1 year';
DELETE FROM media_files WHERE created_at < NOW() - INTERVAL '1 year';
VACUUM;
```

---

## 📚 Architecture Details

For deeper technical information, see **CLAUDE.md** (developer guide).

---

## 🎉 You're Ready!

1. **Verify:** `python verify_echomind.py`
2. **Configure:** Edit `.env` with your database and API keys
3. **Run:** Choose one of the three startup options above
4. **Monitor:** `tail -f logs/echomind.log`
5. **Test:** Add files to `data/manual_uploads/` or send WhatsApp message
6. **Query:** `psql -d echomind -c "SELECT COUNT(*) FROM memory_chunks;"`

**Welcome to EchoMind!** 🧠✨

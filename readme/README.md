# EchoMind

A unified data ingestion platform that aggregates information from multiple communication and productivity services into a centralized, searchable knowledge base.

## Overview

EchoMind integrates with various platforms (WhatsApp, Gmail, Google Meet, Phone, Calendar) to capture, normalize, and analyze communication data. It provides semantic search capabilities through vector embeddings and stores all data in a PostgreSQL database with comprehensive user profiles.

## Features

✨ **Multi-Platform Integration**
- WhatsApp messaging
- Gmail emails
- Google Meet meeting transcripts
- Phone call logs
- Calendar events
- Manual data entry

🔍 **Semantic Search**
- Vector embeddings for intelligent search
- Similarity matching across all sources
- Fast retrieval of relevant information

🔐 **Privacy & Security**
- Secure authentication with each platform
- User-level data isolation
- No sensitive credentials in version control

⚙️ **Automated Processing**
- Scheduled data fetching
- Automatic preprocessing and normalization
- Deduplication and validation

## Architecture

```
┌─────────────────────────────────────────┐
│   External Services (WhatsApp, Gmail)   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   Connectors (Data Normalization)       │
│   - WhatsApp, Gmail, Calendar, etc.     │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   Pipelines (Data Processing)           │
│   - Preprocessing, Embedding, Storage   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   PostgreSQL Database (pgvector)        │
│   - User data, Messages, Embeddings     │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   FastAPI REST API                      │
│   - Query and retrieve data             │
└─────────────────────────────────────────┘
```

## Project Structure

For detailed documentation of each module, see the `readme/` directory:

- **[readme/app/](readme/app/)** - Core application API and logic
- **[readme/connectors/](readme/connectors/)** - Data integration connectors
- **[readme/pipelines/](readme/pipelines/)** - Data processing workflows
- **[readme/services/](readme/services/)** - Microservices (WhatsApp, etc.)
- **[readme/models/](readme/models/)** - Pydantic data models
- **[readme/database/](readme/database/)** - Database schema and management

## Prerequisites

- **Python 3.8+**
- **Node.js 14+** (for WhatsApp service)
- **PostgreSQL 12+** with pgvector extension
- **pip** and **npm** package managers

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/MohammedAbrar2004/echomind.git
cd echomind
```

### 2. Set up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set up Node.js Service

```bash
cd services/whatsapp
npm install
cd ../..
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/echomind
DB_USER=echomind_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=echomind

# API Server
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000

# WhatsApp Configuration
WHATSAPP_TARGET_CHATS=["Contacts","Groups"]
WHATSAPP_POLL_INTERVAL_MINUTES=15
WHATSAPP_SESSION_PATH=./session

# Gmail (optional)
GMAIL_API_KEY=your_google_api_key
GMAIL_USER=your_email@gmail.com

# Google Meet (optional)
GMEET_API_KEY=your_google_api_key

# Logging
LOG_LEVEL=INFO
```

### 5. Initialize Database

```bash
python app/db/init_db.py
```

This will:
- Create the PostgreSQL database
- Initialize schema with all tables
- Set up extensions (pgvector, pgcrypto)

## Running the Project

### Start the Python FastAPI Server

```bash
# Make sure virtual environment is activated
python -m uvicorn app.api.receiver:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at: `http://127.0.0.1:8000`

Health check endpoint: `http://127.0.0.1:8000/health`

### Start the WhatsApp Service (in a separate terminal)

```bash
# Activate Python virtual environment in a new terminal
cd services/whatsapp
npm start
# or: node index.js
```

**First Run Setup**: 
- A QR code will be displayed
- Scan it with your WhatsApp mobile app
- The session will be saved and reused on subsequent runs

### Verify Everything is Running

```bash
# Check API health
curl http://127.0.0.1:8000/health

# You should see: {"status":"ok","service":"EchoMind Receiver"}
```

## API Endpoints

### Health Check
```
GET /health
```

### Ingest WhatsApp Messages
```
POST /ingest/whatsapp
Content-Type: application/json

{
  "messages": [
    {
      "chat_name": "John Doe",
      "message_id": "msg_123",
      "timestamp": "2026-03-29T10:30:00",
      "sender": "john_doe",
      "message": "Hello!",
      "is_group": false
    }
  ]
}
```

## Configuration Details

### WhatsApp Target Chats
Define which chats to monitor by adding their names to the `WHATSAPP_TARGET_CHATS` environment variable:

```env
WHATSAPP_TARGET_CHATS=["Personal Contacts","Work Group","Friends"]
```

### Database Connection
Ensure PostgreSQL is running and accessible:

```bash
# Test PostgreSQL connection
psql -h localhost -U echomind_user -d echomind
```

### Vector Embeddings
The system uses `pgvector` for semantic search. Ensure the extension is installed:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Development

### Running Tests

```bash
# Run Python tests
pytest

# Run with coverage
pytest --cov=app --cov=pipelines --cov=models
```

### Code Style

```bash
# Format code with Black
black .

# Lint with Pylint
pylint app/ pipelines/ models/
```

## Troubleshooting

### Database Connection Errors
- Check PostgreSQL is running: `psql --version`
- Verify `.env` credentials match your PostgreSQL setup
- Ensure pgvector extension is installed

### WhatsApp QR Code Not Appearing
- Clear the session folder: `rm -rf services/whatsapp/session`
- Restart the WhatsApp service
- Scan the new QR code within 30 seconds

### API Not Responding
- Verify the FastAPI server is running on port 8000
- Check firewall settings
- Review logs for errors: `tail -f logs/*.log`

### Missing Dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
cd services/whatsapp && npm install --force
```

## Logging

Logs are written to the `logs/` directory with rotated files:
- `app.log` - Application logs
- `whatsapp.log` - WhatsApp service logs
- `database.log` - Database logs

Adjust log level in `.env`:
```env
LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARNING, ERROR
```

## Contributing

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Commit your changes: `git commit -m 'Add amazing feature'`
3. Push to the branch: `git push origin feature/amazing-feature`
4. Open a Pull Request

## License

This project is private and proprietary.

## Support

For issues, questions, or feature requests, please open an issue on GitHub or contact the development team.

---

**Last Updated**: March 2026

# App Module

The `app/` directory contains the core application logic and APIs for EchoMind.

## Subdirectories

### API (`app/api/`)
- **receiver.py**: FastAPI application that serves as the main REST API endpoint
  - Receives message payloads from Node.js microservices
  - Accepts data from WhatsApp, Gmail, Google Meet, Phone, and Calendar
  - Triggers data ingestion pipeline
  - Health check endpoint available at `/health`
  - Main ingestion endpoint at `/ingest/whatsapp`

### Connectors (`app/connectors/`)
Integration modules for different communication and productivity platforms:
- **base_connector.py**: Abstract base class for all connectors
- **whatsapp_connector.py**: WhatsApp message integration
- **gmail_connector.py**: Gmail email integration
- **gmeet_connector.py**: Google Meet integration
- **phone_connector.py**: Phone call integration
- **calendar_connector.py**: Calendar event integration
- **manual_connector.py**: Manual data entry integration

### Database (`app/db/`)
- **connection.py**: Database connection management
- **init_db.py**: Database initialization script
- **schema.sql**: PostgreSQL schema definition with user profiles and message storage

### Embeddings (`app/embeddings/`)
Handles vector embeddings for semantic search and similarity matching of messages and data.

### Preprocessing (`app/preprocessing/`)
- **preprocessor.py**: Data cleaning, normalization, and preparation for ingestion pipeline

### Scheduler (`app/schedular/`)
- **scheduler.py**: Handles scheduled tasks and periodic data fetching from external services

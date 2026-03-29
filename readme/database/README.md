# Database Module

The `app/db/` directory manages all database operations and schema for EchoMind.

## Overview

The database layer provides:
- Connection pooling and management
- Schema initialization
- Data persistence
- Query optimization

## Components

### Connection Management
**File**: `connection.py`
- PostgreSQL connection pooling
- Connection lifecycle management
- Error handling and retries
- Support for transaction management

### Database Initialization
**File**: `init_db.py`
- Creates schema on first run
- Handles migrations
- Initializes default data
- Validates schema integrity

### Schema Definition
**File**: `schema.sql`

PostgreSQL database schema includes:

#### Users Table
- User profiles with name, email, phone
- Timestamps for tracking
- UUID primary keys

#### User Profile Table
- Extended user information (profession, organization)
- Timezone settings
- Preference summaries

#### Messages Table
- All ingested messages from various sources
- Content, sender, timestamps
- Vector embeddings for semantic search
- Source tracking

#### Additional Tables
- Calendar events
- Emails
- Meeting records
- Contact information

## Setup

### Prerequisites
- PostgreSQL 12+
- pgvector extension for embeddings
- pgcrypto extension for UUID generation

### Initialization
```bash
cd app/db
python init_db.py
```

This will:
1. Connect to PostgreSQL
2. Create all tables
3. Set up extensions
4. Initialize constraints and indexes

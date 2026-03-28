-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

--------------------------------------------------
-- USERS
--------------------------------------------------
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone_number TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- USER PROFILE
--------------------------------------------------
CREATE TABLE user_profile (
    user_id UUID PRIMARY KEY
        REFERENCES users(id) ON DELETE CASCADE,
    profession TEXT,
    organization TEXT,
    timezone TEXT,
    preferences_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- DATA SOURCES
--------------------------------------------------
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ingestion_mode TEXT NOT NULL
        CHECK (ingestion_mode IN ('scheduled','manual')),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- USER INTEGRATIONS
--------------------------------------------------
CREATE TABLE user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    encrypted_credentials TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, tool_name)
);

--------------------------------------------------
-- SESSIONS
--------------------------------------------------
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL
        REFERENCES users(id) ON DELETE RESTRICT,
    topic_hint TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- MEMORY CHUNKS
--------------------------------------------------
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL
        REFERENCES users(id) ON DELETE RESTRICT,
    source_id UUID NOT NULL
        REFERENCES data_sources(id) ON DELETE RESTRICT,
    external_message_id TEXT NOT NULL,
    session_id UUID
        REFERENCES sessions(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    participants JSONB,
    content_type TEXT NOT NULL
        CHECK (content_type IN ('text','transcript','email','document')),
    raw_content TEXT NOT NULL,
    embedding VECTOR(1536),
    initial_salience FLOAT NOT NULL DEFAULT 0,
    refined_salience FLOAT,
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_id, external_message_id)
);

--------------------------------------------------
-- INGESTION RUNS
--------------------------------------------------
CREATE TABLE ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL
        REFERENCES data_sources(id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL
        CHECK (status IN ('running','success','failed','partial')),
    records_fetched INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- PROCESSING QUEUE
--------------------------------------------------
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_chunk_id UUID NOT NULL
        REFERENCES memory_chunks(id) ON DELETE CASCADE,
    status TEXT NOT NULL
        CHECK (status IN ('pending','processing','done','failed','retry')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(memory_chunk_id)
);

--------------------------------------------------
-- SYSTEM LOGS
--------------------------------------------------
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level TEXT NOT NULL
        CHECK (level IN ('info','warning','error','critical')),
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- FAILED JOBS
--------------------------------------------------
CREATE TABLE failed_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL
        CHECK (job_type IN ('ingestion','semantic_processing','retrieval','action')),
    reference_id UUID,
    failure_reason TEXT,
    retry_attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------
-- SCHEDULER STATE
--------------------------------------------------
CREATE TABLE scheduler_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID
        REFERENCES data_sources(id) ON DELETE SET NULL,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    last_started_at TIMESTAMPTZ,
    heartbeat_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
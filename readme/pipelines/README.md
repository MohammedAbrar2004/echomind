# Pipelines Module

The `pipelines/` directory contains data processing workflows that transform raw input into structured, actionable data.

## Overview

Pipelines handle the complete data flow from raw input to storage:
- Data validation and normalization
- Deduplication and cleaning
- Embedding generation for semantic search
- Storage in the database
- Error handling and logging

## Ingestion Pipeline

**File**: `ingestion_pipeline.py`

The main ingestion pipeline orchestrates the complete data processing workflow:

### Stages
1. **Receive**: Accept normalized data from connectors
2. **Preprocess**: Clean and validate data
3. **Embed**: Generate vector embeddings for semantic search
4. **Deduplicate**: Remove duplicate entries
5. **Store**: Save to database

### Usage
```python
from pipelines.ingestion_pipeline import run_ingestion_for_items

# Run ingestion on a list of items
run_ingestion_for_items(normalized_items)
```

### Key Features
- Handles multiple data types (messages, emails, calendar events, etc.)
- Batch processing for efficient database operations
- Transaction management for data integrity
- Comprehensive error logging

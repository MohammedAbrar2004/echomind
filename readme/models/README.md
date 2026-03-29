# Models Module

The `models/` directory contains Pydantic data models used throughout EchoMind for data validation and serialization.

## Overview

Models define the structure and validation rules for data flowing through the system.

## Models

### Normalized Input
**File**: `normalized_input.py`

Defines the standard data model for all ingested information:
- Ensures consistent structure across all data sources
- Validates required fields
- Handles type conversion
- Provides documentation for API consumers

### Key Features
- Pydantic-based for automatic validation
- JSON schema generation
- Type hints for IDE support
- Serialization/deserialization utilities

## Usage

```python
from models.normalized_input import NormalizedMessage

# Create and validate data
message = NormalizedMessage(
    source="whatsapp",
    sender="john_doe",
    content="Hello world",
    timestamp="2026-03-29T10:30:00"
)

# Convert to dict
data = message.dict()
```

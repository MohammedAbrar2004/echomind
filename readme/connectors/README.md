# Connectors Module

The `app/connectors/` module provides integration interfaces for multiple communication and productivity platforms.

## Overview

Connectors are responsible for:
- Fetching data from external services (push or pull)
- Normalizing data into a standard format
- Handling authentication and API interactions
- Error handling and retry logic

## Available Connectors

### Base Connector
**File**: `base_connector.py`
- Abstract base class that all connectors inherit from
- Defines the standard interface for data fetching and normalization
- Handles common functionality across all integrations

### WhatsApp Connector
**File**: `whatsapp_connector.py`
- Receives messages via webhook from Node.js service
- Supports individual and group chats
- Extracts sender, timestamp, and message content

### Gmail Connector
**File**: `gmail_connector.py`
- Integrates with Gmail API
- Fetches emails and attachments
- Handles email threading and conversations

### Google Meet Connector
**File**: `gmeet_connector.py`
- Integrates Google Meet API
- Captures meeting metadata and transcripts
- Handles participant information

### Phone Connector
**File**: `phone_connector.py`
- Integrates phone call logs and transcripts
- Handles call metadata (duration, participants, etc.)

### Calendar Connector
**File**: `calendar_connector.py`
- Integrates Google Calendar API
- Fetches event details and attendee information
- Handles recurring events

### Manual Connector
**File**: `manual_connector.py`
- Handles manual data entry through API
- Allows direct input of information not captured automatically

## Usage

Each connector can be instantiated and used to fetch data:
```python
from app.connectors.whatsapp_connector import WhatsAppConnector

connector = WhatsAppConnector()
normalized_data = connector.fetch_from_push(message_data)
```

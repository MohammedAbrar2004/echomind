# Services Module

The `services/` directory contains microservices that handle specific integrations and external communications.

## WhatsApp Service

**Directory**: `services/whatsapp/`

A Node.js-based microservice for WhatsApp integration using WhatsApp Web API.

### Components

#### Configuration
- **config.js**: Centralized configuration management
  - Target chats (which chats to monitor)
  - Poll interval for message fetching
  - Session path for authentication
  - Receiver API endpoint URL

#### Main Service
- **index.js**: Entry point and main bot logic
- **sender.js**: Sends messages via WhatsApp
- **package.json**: Node.js dependencies

### Workflow
1. Monitors WhatsApp chats for new messages
2. Polls at configured intervals
3. Sends received messages to Python FastAPI receiver
4. Maintains session authentication in `session/` folder (ignored in Git)

### Setup
See the main README for WhatsApp setup instructions using the `.env` file:
```
WHATSAPP_TARGET_CHATS=["chat1", "chat2"]
WHATSAPP_POLL_INTERVAL_MINUTES=15
WHATSAPP_SESSION_PATH=./session
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000
```

### Running
```bash
cd services/whatsapp
npm install
node index.js
```

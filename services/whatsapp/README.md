# EchoMind WhatsApp Service (Baileys)

## Status

✅ **Active** — Baileys socket, QR authentication, real-time message ingestion, and media download all working.

---

## Quick Start

### Prerequisites

- Node.js 16+
- `.env` file with configuration (see below)
- WhatsApp device for QR scanning

### Installation

```bash
cd services/whatsapp
npm install
```

### Configuration

Update your root `.env` file:

```env
# WhatsApp Service
WHATSAPP_TARGET_CHATS=["919XXXXXXXXXX@s.whatsapp.net"]  # JIDs of target chats
WHATSAPP_POLL_INTERVAL_MINUTES=30
WHATSAPP_SESSION_PATH=./session

# FastAPI Receiver
RECEIVER_HOST=127.0.0.1
RECEIVER_PORT=8000
```

**Note on WHATSAPP_TARGET_CHATS:**
- Use WhatsApp Web JIDs — `919XXXXXXXXXX@s.whatsapp.net` (individual) or `120363XXXXXX@g.us` (group)
- `[]` accepts all chats — use this on first run to discover JIDs from the `CHAT JID:` log line, then update `.env`

### Running the Service

```bash
npm start
```

Expected output on first run:

```
[WhatsApp] ==================================================================
[WhatsApp] EchoMind WhatsApp Service (Baileys)
[WhatsApp] ==================================================================
[WhatsApp] ℹ Receiver URL: http://127.0.0.1:8000
[WhatsApp] ℹ Target Chats: 120363418805460865@g.us
[WhatsApp] ℹ Session Path: ./session
[WhatsApp] ℹ Media Size Limit: 50 MB
[WhatsApp] ==================================================================
[WhatsApp] Opening socket and attempting connection (attempt 1/3)...
[WhatsApp] Initializing Baileys WhatsApp client...
[WhatsApp] ℹ Using session directory: .../services/whatsapp/session
[WhatsApp] ℹ WA version: 2.3000.XXXXXXXXX, latest: true
[WhatsApp] ℹ Connecting to WhatsApp...

<QR Code appears here on first run — scan with WhatsApp>

[WhatsApp] Scan QR code above to authenticate
[WhatsApp] ✓ Connected to WhatsApp
[WhatsApp] ℹ Listening for real-time messages...
```

---

## How It Works

### 1. Authentication (One-Time)

1. Service starts
2. Checks for session in `./session/` folder
3. If no session → QR appears in terminal
4. Scan QR with WhatsApp phone
5. Session saved automatically
6. Connection opens

On subsequent restarts: Session loads automatically, no QR needed

### 2. Message Ingestion

Messages arrive via:
- **Real-time**: `messages.upsert` event (new incoming messages)

Each message is:
1. Normalized into `NormalizedInput` format
2. Sent to FastAPI receiver at `/ingest/whatsapp`
3. Processed through ingestion pipeline
4. Stored in PostgreSQL

### 3. Media Handling

Supported media types:
- Images (JPEG, PNG, etc.)
- Audio (MP3, voice notes, etc.)
- Video
- Documents (PDF, DOCX, etc.)

Media is:
1. Downloaded from WhatsApp servers
2. Converted to base64
3. Size-checked (max 50MB)
4. Sent with message to FastAPI
5. Saved by `MediaService` to `/media` folders

---

## Project Structure

```
services/whatsapp/
├── index.js              (Main service)
├── config.js             (Load .env)
├── sender.js             (HTTP POST to FastAPI receiver)
├── package.json          (Dependencies)
├── session/              (Session folder - appears after first auth)
│   ├── creds.json
│   ├── pre-keys.json
│   ├── sessions.json
│   └── ...
└── node_modules/
```

---

## Debugging

### Issue: Connection closes before QR appears

**Symptoms:**
- "Connection closed: Connection Failure" in logs
- No QR displayed
- Session folder empty

**Causes:**
1. Network blocking WebSocket
2. Outdated Baileys version
3. Bad configuration

**Fix:**

1. Verify socket config includes browser fingerprint and version (check `index.js`):
   ```javascript
   const { version } = await fetchLatestBaileysVersion();
   const sock = makeWASocket({
     auth: state,
     version,
     browser: Browsers.ubuntu("Chrome"),
     logger: logger,
   });
   ```

2. Delete session folder and retry:
   ```bash
   rm -r ./session
   ```

3. Try a different network (mobile hotspot instead of WiFi)

4. Check firewall allows Node.js WebSocket connections

### Issue: QR appears but scanning doesn't work

**Cause:** Network issue during auth, or QR expired (30min)

**Fix:**
- Delete session folder
- Try scanning again
- Check connection stability

### Issue: Service keeps disconnecting and reconnecting

**Cause:** Unstable network or bad WiFi

**Fix:**
- Check WiFi signal strength
- Try ethernet or mobile hotspot
- Check router firewall settings

### Issue: Session folder shows files but no messages received

**Cause:** Messages may not be arriving, or filtering is removing them

**Fix:**
1. Verify target chats config:
   ```bash
   # Check .env
   cat ../../.env | grep WHATSAPP_TARGET_CHATS
   ```

2. Send a test message from WhatsApp to tracked chat

3. Check FastAPI receiver logs:
   ```bash
   # In another terminal, check if messages arrive at receiver
   ```

4. Check PostgreSQL:
   ```sql
   SELECT COUNT(*) FROM memory_chunks WHERE source = 'whatsapp';
   ```

---

## How to Get Chat JID

To find the JID of a WhatsApp chat:

1. Set `WHATSAPP_TARGET_CHATS=[]` in `.env` (accept all chats)
2. Start the service and scan the QR code
3. Send a test message from the chat you want to track
4. The service will log:
   ```
   [WhatsApp] CHAT JID: 120363418805460865@g.us
   ```
5. Copy that JID into `.env`:
   ```env
   WHATSAPP_TARGET_CHATS=["120363418805460865@g.us"]
   ```
6. Restart the service

Example JID formats:
- Individual: `919876543210@s.whatsapp.net`
- Group: `120622XXXXXXXXX-XXXXXXXXX@g.us`

Then update `.env`:
```env
WHATSAPP_TARGET_CHATS=["919876543210@s.whatsapp.net"]
```

---

## Architecture: How Data Flows

```
WhatsApp Device
    ↓ (QR scan, session established)
    ↓
Baileys Socket (WebSocket connection to WhatsApp Web)
    ↓ (messages.upsert event)
    ↓
processMessage() function (normalize to NormalizedInput)
    ↓ (media download, base64 encoding)
    ↓
sendMessages() via HTTP POST
    ↓
FastAPI Receiver (/ingest/whatsapp)
    ↓
WhatsAppConnector.fetch_from_push()
    ↓ (media extraction, normalization)
    ↓
ingestion_pipeline.run_ingestion()
    ↓ (preprocessing, deduplication)
    ↓
PostgreSQL (memory_chunks, media_files tables)
    ↓
Ready for Layer 3 (Semantic Extraction)
```

---

## Current Implementation Details

### Socket Configuration

```javascript
const { version } = await fetchLatestBaileysVersion();
const sock = makeWASocket({
  auth: state,                    // Session persistence
  version,                        // Current WA Web protocol version
  browser: Browsers.ubuntu("Chrome"), // Browser fingerprint accepted by WA servers
  logger: logger,                 // Pino logger (silent in production)
});
```

### Session Persistence

```javascript
sock.ev.on("creds.update", saveCreds);
```

- Credentials saved automatically after each auth event
- Session folder persists across service restarts
- No re-authentication required (until logged out)

### Connection Lifecycle

```javascript
sock.ev.on("connection.update", ({ connection, qr, lastDisconnect }) => {
  if (qr) { /* display QR */ }
  if (connection === "open") { /* start ingesting */ }
  if (connection === "close") { /* reconnect */ }
});
```

### Message Ingestion

```javascript
sock.ev.on("messages.upsert", ({ messages, type }) => {
  if (type === "notify") {
    messages
      .filter(m => !m.key.fromMe)  // Skip outgoing
      .forEach(m => processMessage(m));
  }
});
```

### Chat Filtering

```javascript
// targetChats supports both individual and group JIDs
// Empty array = accept all chats
if (targetChats.length > 0 && !targetChats.includes(from)) return;
```

### Reconnection Strategy

```javascript
// Exponential backoff: 1s, 3s, 5s retries
if (connection closed) {
  retry with BACKOFF_MS
}
```

---

## What's NOT Implemented Yet

- ⏳ Calendar connector
- ⏳ Google Meet integration
- ⏳ Layer 3+ (semantic extraction, retrieval, response generation)

---

## Troubleshooting Checklist

- [ ] `WHATSAPP_SESSION_PATH=./session` in `.env` (relative to `services/whatsapp/`)
- [ ] Socket config has `version`, `browser: Browsers.ubuntu("Chrome")`, and `logger`
- [ ] `creds.update` event registers `saveCreds`
- [ ] Network allows WebSocket connections
- [ ] FastAPI receiver running on port 8000
- [ ] If still failing: delete `./session/` folder and retry

---

## Logs & Monitoring

Service logs to console. For persistent logging setup:

```bash
npm start >> ./whatsapp-service.log 2>&1 &
tail -f ./whatsapp-service.log
```

Log prefix: `[WhatsApp]`

---

## Security Notes

⚠️ **Session folder contains full account access:**
- Add to `.gitignore`: `services/whatsapp/session/`
- Never commit session files
- Treat like a password

⚠️ **Account risk:**
- Baileys is unofficial → WhatsApp may restrict account
- Don't spam or abuse
- Keep message processing reasonable
- Consider this for MVP only

---

## Next Steps (Future Work)

1. **Phase 2**: Offline message recovery logic
2. **Phase 3**: Automated JID discovery from .env chat names
3. **Phase 4**: Integration tests with fixtures
4. **Phase 5**: Calendar, GMeet, Manual connectors
5. **Phase 6+**: Layer 3-5 implementation

---

## References

- [Baileys GitHub](https://github.com/whiskeysockets/Baileys)
- [Baileys Wiki](https://baileys.wiki)
- [EchoMind BAILEYS_GUIDE.md](../../BAILEYS_GUIDE.md) — Comprehensive Baileys reference
- [CLAUDE.md](../../CLAUDE.md) — Project overview

---

**Last Updated:** April 2026  
**Status:** Active

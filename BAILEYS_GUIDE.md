# BAILEYS WHATSAPP LIBRARY — ECHOMIND IMPLEMENTATION GUIDE

> Concise, practical documentation for EchoMind WhatsApp ingestion via Baileys

---

## 1. WHAT IS BAILEYS?

Baileys is a **reverse-engineered WhatsApp Web WebSocket client** written in TypeScript/JavaScript.

### Key Characteristics

- **Not Official**: WhatsApp does not support this → can break anytime
- **WebSocket-based**: Real-time bidirectional communication (not HTTP)
- **Session-based**: One-time QR auth, persisted via multi-file state
- **Event-driven**: Asynchronous message and connection events
- **Unreliable**: No SLA, no rate limits, possible account restrictions

### Architecture Flow

```
Your Node.js Service
    ↓
  Baileys Socket (WebSocket)
    ↓
  WhatsApp Web Servers
    ↓
  Real-time Events (messages, auth, status)
```

---

## 2. INSTALLATION & SETUP

### Install Baileys

```bash
npm install @whiskeysockets/baileys
```

### Import Required Functions

```javascript
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  isJidGroup,
  downloadMediaMessage,
} = require("@whiskeysockets/baileys");
```

### Required Dependencies

- **pino** (logger): `npm install pino`
- **qrcode-terminal** (QR display): `npm install qrcode-terminal` (if printQRInTerminal: false)
- **dotenv** (env vars): `npm install dotenv`
- **axios** (HTTP): `npm install axios`

---

## 3. AUTHENTICATION MODEL

### Multi-File Auth State

```javascript
const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
```

**What it does:**
- Creates individual files in `sessionDir` for each auth component
- Files contain encryption keys, tokens, device identity
- On first run → empty state (QR required)
- On restart → loads saved state (auto login)

**Files created in session directory:**
```
session/
  creds.json       (credentials & keys)
  pre-keys.json    (pre-key data)
  sessions.json    (active sessions)
  app-state-sync-key.json
  app-state-sync-version.json
  sender-key-memory.json
  sender-key.json
  signal-identities.json
  signal-keys.json
```

### Authentication Flow

```
Start Service
    ↓
  Load Session (or empty)
    ↓
  Create Socket
    ↓
  No Creds? → QR Event Fires
    ↓
  User Scans QR
    ↓
  creds.update Event
    ↓
  Save Credentials
    ↓
  Connection Opens (connection.update: open)
```

### Critical Rules

1. **Never commit session folder** → Add to .gitignore
2. **Never delete session** unless re-authentication needed
3. **Always call saveCreds** in creds.update event
4. **Session = Account Access** → Treat like password

---

## 4. SOCKET INITIALIZATION

### Minimal Configuration (Recommended)

```javascript
const logger = pino({ level: "silent" }); // suppress Baileys logs

const sock = makeWASocket({
  auth: state,
  printQRInTerminal: true,
  logger: logger,
});
```

### Why "Minimal"?

- Avoids browser fingerprint issues
- Reduces compatibility problems
- Lets Baileys use sensible defaults
- More stable across versions

### What NOT to Include

❌ `browser: ["EchoMind", "Safari", "2.0.0"]` — can cause fingerprint rejection  
❌ `syncFullHistory: true` — unnecessary for new messages  
❌ `maxMsgRetryCount: 3` — default is fine  
❌ `version: [...]` — auto-detected  

---

## 5. SESSION PATH CONFIGURATION

### Rule: Use Relative Paths

Since your Node service runs from inside `services/whatsapp/`:

```env
# .env (correct)
WHATSAPP_SESSION_PATH=./session
```

**NOT:**
```env
# .env (wrong)
WHATSAPP_SESSION_PATH=./services/whatsapp/session
```

### In Code

```javascript
const sessionDir = path.resolve(sessionPath);
```

The `path.resolve()` converts relative to absolute correctly.

---

## 6. CONNECTION LIFECYCLE

### Main Event: connection.update

```javascript
sock.ev.on("connection.update", ({ connection, qr, lastDisconnect }) => {
  // Handle state changes
});
```

### States & Handling

#### QR Generation
```javascript
if (qr) {
  // QR only appears if no session exists
  const qrcode = require("qrcode-terminal");
  qrcode.generate(qr, { small: true });
  console.log("Scan QR code above with WhatsApp device");
}
```

#### Connecting
```javascript
if (connection === "connecting") {
  console.log("Attempting to connect to WhatsApp...");
}
```

#### Connected (Success)
```javascript
if (connection === "open") {
  console.log("✓ Connected to WhatsApp");
  // Start ingesting messages
}
```

#### Disconnected
```javascript
if (connection === "close") {
  const shouldReconnect =
    lastDisconnect?.error?.output?.statusCode !==
    DisconnectReason.loggedOut;

  if (shouldReconnect) {
    console.log("Connection lost, attempting reconnect...");
    // Retry with backoff
  } else {
    console.error("Logged out, QR required");
    // User needs to re-authenticate
  }
}
```

### Disconnect Reason Codes

| Code | Meaning | Action |
|------|---------|--------|
| loggedOut | Session invalid | Require QR |
| connectionClosed | Network dropped | Retry |
| connectionReplaced | Other device connected | Retry |
| connectionLost | WebSocket timeout | Retry |
| restartRequired | Protocol needs update | Restart service |

---

## 7. MESSAGE INGESTION

### Event Handler

```javascript
sock.ev.on("messages.upsert", ({ messages, type }) => {
  if (type === "notify") { // Only new incoming messages
    for (const msg of messages) {
      if (!msg.key.fromMe) { // Skip outgoing
        processMessage(msg);
      }
    }
  }
});
```

### Message Object Structure

```
msg.key
  ├─ remoteJid        (STRING) — chat id e.g., "919XXXXXXX@s.whatsapp.net"
  ├─ fromMe           (BOOL) — true if sent by you
  ├─ id               (STRING) — unique message id
  ├─ participant      (STRING) — sender (group only)
  └─ _serialized      (STRING) — internal

msg.message
  ├─ conversation              (TEXT) — plain text
  ├─ extendedTextMessage       (OBJ) — text with formatting
  │   └─ text
  ├─ imageMessage              (OBJ) — image
  │   ├─ mimetype
  │   ├─ caption
  │   └─ imageData (large object)
  ├─ audioMessage              (OBJ) — voice/audio
  │   ├─ mimetype
  │   └─ audioData
  ├─ videoMessage              (OBJ) — video
  │   ├─ caption
  │   ├─ mimetype
  │   └─ videoData
  ├─ documentMessage           (OBJ) — files
  │   ├─ fileName
  │   ├─ mimetype
  │   └─ documentData
  └─ [other types]

msg.messageTimestamp          (NUMBER) — Unix timestamp
msg.pushName                  (STRING) — sender name
```

### Extracting Text Content

```javascript
const messageText = msg.message?.conversation ||
                   msg.message?.extendedTextMessage?.text ||
                   "[Media message]";
```

### Extracting Sender Name

```javascript
const sender = msg.pushName || msg.key.participant || "Unknown";
```

### Extracting Chat ID

```javascript
const chatId = msg.key.remoteJid;
```

---

## 8. CHAT FILTERING

### WRONG Approach ❌

```javascript
// sock.getChat() does NOT exist
const chat = await sock.getChat(remoteJid); // ERROR!
```

### CORRECT Approach ✅

#### Method A: JID-Based Filtering (RECOMMENDED)

```javascript
const targetChats = [
  "919XXXXXXX@s.whatsapp.net",  // Individual
  "120622XXXXXXXXX-XXXXXXXXX@g.us", // Group
];

if (!targetChats.includes(msg.key.remoteJid)) {
  return; // Skip chat not in list
}
```

**Advantages:**
- JIDs are unique and stable
- Always available in message
- Reliable across provider changes

#### Method B: Get All Chats (if needed)

```javascript
const chats = await sock.getChats();
// Returns array of all chats with metadata
```

**Warning:** This is slow for large chat lists. Use sparingly.

#### Method C: Combine With Offline Recovery

```javascript
const chats = await sock.getChats();
const targetChat = chats.find(c => c.id === desiredJid);

if (targetChat) {
  const messages = await sock.loadMessages(targetChat.id, 50);
  // Process messages
}
```

---

## 9. MEDIA HANDLING

### Download Media

```javascript
const buffer = await downloadMediaMessage(msg, "buffer", {}, logger);
```

**Parameters:**
- `msg` — the message object
- `"buffer"` — return type (Buffer, stream, url)
- `{}` — options object
- `logger` — pino logger instance

### Convert to Base64

```javascript
const base64String = buffer.toString("base64");
```

### Size Limiting

```javascript
const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

if (buffer.length > MAX_SIZE) {
  console.warn("Media too large, skipping");
  return;
}
```

### Error Handling

```javascript
try {
  const buffer = await downloadMediaMessage(msg, "buffer", {}, logger);
  if (buffer) {
    mediaData = buffer.toString("base64");
  }
} catch (err) {
  console.warn(`Failed to download media: ${err.message}`);
  // Continue without media
}
```

### Detecting Media Type

```javascript
let mediaType = null;

if (msg.message?.imageMessage) {
  mediaType = msg.message.imageMessage.mimetype; // e.g., "image/jpeg"
}
if (msg.message?.audioMessage) {
  mediaType = msg.message.audioMessage.mimetype;
}
if (msg.message?.videoMessage) {
  mediaType = msg.message.videoMessage.mimetype;
}
if (msg.message?.documentMessage) {
  mediaType = msg.message.documentMessage.mimetype;
}
```

---

## 10. STATE PERSISTENCE

### Save Credentials On Update

```javascript
sock.ev.on("creds.update", saveCreds);
```

**Why critical:**
- Without this, session is lost on restart
- QR required every service restart
- User must re-authenticate constantly

### Implement saveState Function

```javascript
function saveCreds() {
  // useMultiFileAuthState handles this automatically
  // Just ensure you call it in the event handler
}
```

---

## 11. HANDLING GROUP MESSAGES

### Detect Groups

```javascript
if (isJidGroup(msg.key.remoteJid)) {
  // This is a group message
  console.log("Group:", msg.key.remoteJid);
  console.log("Sender:", msg.key.participant);
} else {
  // This is an individual message
  console.log("Individual chat:", msg.key.remoteJid);
}
```

### Filter Groups (if needed)

```javascript
if (isJidGroup(msg.key.remoteJid)) {
  return; // Skip groups
}
```

---

## 12. RECONNECTION STRATEGY

### Implement Retry With Exponential Backoff

```javascript
const MAX_ATTEMPTS = 3;
const BACKOFF_MS = [1000, 3000, 5000]; // 1s, 3s, 5s

async function main() {
  let attempts = 0;

  while (attempts < MAX_ATTEMPTS) {
    try {
      const sock = await initializeSocket();
      // Socket connected successfully
      break;
    } catch (err) {
      attempts++;
      if (attempts < MAX_ATTEMPTS) {
        const delay = BACKOFF_MS[attempts - 1];
        console.log(`Retrying in ${delay}ms...`);
        await sleep(delay);
      } else {
        console.error("Max retry attempts reached");
        process.exit(1);
      }
    }
  }
}
```

---

## 13. COMMON FAILURE MODES

### Failure 1: Connection Closes Before QR

**Symptoms:**
- "Connection Failure" in logs
- No QR displayed
- Session folder empty

**Causes:**
- Network blocking WebSocket
- Outdated Baileys version
- Bad socket configuration
- WhatsApp protocol change

**Debug Steps:**
1. Verify `printQRInTerminal: true`
2. Use minimal socket config only
3. Delete session folder
4. Update Baileys: `npm install @whiskeysockets/baileys@latest`
5. Try different network (mobile hotspot instead of WiFi)

### Failure 2: Empty Session Folder After QR

**Symptoms:**
- QR appears but scanning doesn't work
- creds.update never fires
- Session folder stays empty

**Causes:**
- QR scan failed
- Connection dropped before auth completed

**Fix:**
- Delete session folder
- Try QR again
- Check network stability

### Failure 3: Infinite Reconnect Loop

**Symptoms:**
- Service starts, connects, disconnects, repeats
- High CPU usage

**Causes:**
- Protocol mismatch
- Unstable network
- Bad disconnect handler logic

**Fix:**
- Increase backoff delays
- Add jitter to prevent thundering herd
- Check network connection

---

## 14. ECHOMIND INTEGRATION REQUIREMENTS

Your WhatsApp connector MUST:

### ✅ Authentication
- [ ] Load session from `./session`
- [ ] Save credentials on update
- [ ] Display QR for new devices
- [ ] Handle loggedOut case

### ✅ Message Ingestion
- [ ] Filter only target chats (via JID)
- [ ] Skip outgoing messages (`msg.key.fromMe`)
- [ ] Extract text content
- [ ] Detect and download media
- [ ] Enforce 50MB media limit

### ✅ Normalization
Create NormalizedInput with:
```javascript
{
  chat_name: remoteJid,
  message_id: msg.key.id,
  timestamp: ISO8601,
  sender: senderName,
  message: messageText,
  is_group: false/true,
  has_media: true/false,
  media_data: base64String, // if media
  media_mime_type: "image/jpeg", // if media
}
```

### ✅ Forwarding
- POST normalized messages to FastAPI receiver
- Handle failures gracefully
- Implement retry logic

### ✅ Reliability
- Reconnect on disconnect (except loggedOut)
- Persistent logging
- Graceful shutdown on signals

---

## 15. DEBUGGING CHECKLIST

If connection fails:

- [ ] Session path is `./session` in .env?
- [ ] Socket config is minimal (only auth, printQRInTerminal, logger)?
- [ ] `creds.update` event registers `saveCreds`?
- [ ] Removed browser config?
- [ ] Network allows WebSocket? (check firewall)
- [ ] Baileys version is latest?
- [ ] Session folder deleted before testing?
- [ ] Trying different network (mobile hotspot)?

---

## 16. BEST PRACTICES

### ✅ DO

- Keep session local → never commit
- Process messages async → don't block event handler
- Filter early → skip unwanted chats
- Log connection state changes
- Handle both text and media
- Implement proper error boundaries

### ❌ DON'T

- Store session in repo
- Use undocumented methods
- Over-configure socket
- Assume stability like official API
- Block event handlers with sync operations
- Ignore auth state changes

---

## 17. EXPECTED SUCCESS FLOW

```
npm start
    ↓
Display QR
    ↓
User scans QR (with WhatsApp phone)
    ↓
connection.update: open event
    ↓
creds.update fires (credentials saved)
    ↓
Session folder populated
    ↓
messages.upsert events stream in
    ↓
Messages normalized and sent to FastAPI
    ↓
Data appears in PostgreSQL
```

**Success indicators:**
- Session folder has files
- Logs show "✓ Connected to WhatsApp"
- Incoming messages appear in console
- Messages reach FastAPI endpoint

---

## 18. QUICK REFERENCE

### Socket Setup
```javascript
const sock = makeWASocket({
  auth: state,
  printQRInTerminal: true,
  logger: pino({ level: "silent" }),
});
```

### Save Creds
```javascript
sock.ev.on("creds.update", saveCreds);
```

### Handle Connection
```javascript
sock.ev.on("connection.update", ({ connection, qr }) => {
  if (qr) console.log("Scan QR");
  if (connection === "open") console.log("Connected");
  if (connection === "close") handleReconnect();
});
```

### Ingest Messages
```javascript
sock.ev.on("messages.upsert", ({ messages, type }) => {
  if (type === "notify") {
    messages
      .filter(m => !m.key.fromMe)
      .forEach(m => processMessage(m));
  }
});
```

### Download Media
```javascript
const buffer = await downloadMediaMessage(msg, "buffer", {}, logger);
const base64 = buffer.toString("base64");
```

### Filter Chats
```javascript
if (!targetChats.includes(msg.key.remoteJid)) return;
```

---

## 19. LIMITATIONS & WARNINGS

- **Not Official**: WhatsApp doesn't provide/support this
- **Can Break**: Any protocol update can break Baileys
- **Rate Limits**: No guarantees, WhatsApp may restrict
- **Ban Risk**: Excessive use may trigger account restrictions
- **No SLA**: No uptime guarantees
- **Fragile**: Depends on reverse engineering

---

## 20. SUPPORT & DEBUGGING

If you encounter issues:

1. Check this guide first
2. Review Baileys GitHub issues: https://github.com/whiskeysockets/Baileys
3. Read Baileys wiki: https://baileys.wiki
4. Isolate to minimal config and test again
5. Try different network

---

**Document Version:** 1.0  
**For EchoMind WhatsApp Connector**  
**Last Updated:** April 2026

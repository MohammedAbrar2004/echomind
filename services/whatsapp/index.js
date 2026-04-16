const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const fs = require("fs");
const { targetChats, sessionPath } = require("./config");
const { sendMessages } = require("./sender");

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const STATE_FILE = "./whatsapp_state.json";

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
    }
  } catch (e) {
    console.warn("[WhatsApp] Could not load state file, starting fresh.");
  }
  return {};
}

function saveState(state) {
  try {
    fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), "utf8");
  } catch (e) {
    console.error("[WhatsApp] Could not save state file:", e.message);
  }
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const lastFetchTime = loadState();
const processedMessageIds = new Set();

// ============================================================================
// CLIENT INITIALIZATION
// ============================================================================

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: sessionPath }),
  puppeteer: {
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    protocolTimeout: 120000,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--no-first-run",
      "--no-default-browser-check",
    ],
  },
});

// ============================================================================
// EVENT HANDLERS
// ============================================================================

client.on("qr", (qr) => {
  console.log("[WhatsApp] Scan QR code to authenticate:");
  qrcode.generate(qr, { small: true });
});

client.on("ready", async () => {
  console.log("[WhatsApp] Client ready.");
  console.log(`[WhatsApp] Monitoring chats: ${targetChats.join(", ")}`);
  console.log("[WhatsApp] Event listener is active for real-time messages");

  // CRITICAL: Wait 30 seconds for WhatsApp Web to fully initialize
  console.log(
    "[WhatsApp] Waiting 30 seconds for WhatsApp Web to fully initialize..."
  );
  await sleep(30000);

  // Attempt initial fetch (non-blocking, optional)
  console.log("[WhatsApp] Attempting initial fetch for offline messages...");
  initialFetch().catch((err) => {
    console.warn(
      "[WhatsApp] Initial fetch failed (this is OK, event listener is active):",
      err.message
    );
  });
});

client.on("auth_failure", (msg) => {
  console.error(`[WhatsApp] Auth failed: ${msg}`);
});

client.on("disconnected", (reason) => {
  console.warn(`[WhatsApp] Disconnected: ${reason}`);
});

// Real-time message listener (primary mechanism)
client.on("message", async (msg) => {
  const chatName = msg._data.notifyName || msg.pushname || msg.from;

  if (!targetChats.includes(chatName)) {
    return;
  }

  // Skip if already processed
  const msgId = msg.id._serialized;
  if (processedMessageIds.has(msgId)) {
    return;
  }
  processedMessageIds.add(msgId);

  console.log(`[WhatsApp] ⬇ Message from: ${chatName}`);
  await processMessage(msg, chatName);
});

// ============================================================================
// MESSAGE PROCESSING
// ============================================================================

async function processMessage(msg, chatName) {
  try {
    const hasText = typeof msg.body === "string" && msg.body.trim() !== "";

    // Skip messages with no text
    if (!hasText) {
      return;
    }

    // Normalize and send to FastAPI
    const normalized = [
      {
        chat_name: chatName,
        message_id: msg.id._serialized,
        timestamp: new Date(msg.timestamp * 1000).toISOString(),
        sender:
          msg._data.notifyName || msg.pushname || msg.from || "unknown",
        message: msg.body,
        is_group: msg.isGroup || false,
      },
    ];

    await sendMessages(normalized);
    console.log(`[WhatsApp] ✓ Sent message to FastAPI`);

    // Update last fetch time
    lastFetchTime[chatName] = msg.timestamp * 1000;
    saveState(lastFetchTime);
  } catch (err) {
    console.error(`[WhatsApp] Error processing message: ${err.message}`);
  }
}

// ============================================================================
// SAFE MESSAGE FETCHING (with rehydration + retry)
// ============================================================================

async function safeFetchMessages(chat, chatName) {
  /**
   * Safe wrapper around chat.fetchMessages()
   * - Try to fetch messages
   * - On failure: rehydrate chat using getChatById and retry once
   * - Prevents "waitForChatLoading" errors
   */

  try {
    console.log(`[WhatsApp] Fetching messages from: ${chatName}`);
    const messages = await chat.fetchMessages({ limit: 20 });
    return messages;
  } catch (err) {
    console.warn(
      `[WhatsApp] First fetch attempt failed for "${chatName}": ${err.message}`
    );

    try {
      // Attempt to rehydrate the chat object
      console.log(`[WhatsApp] Rehydrating chat: ${chatName}`);
      const rehydratedChat = await client.getChatById(chat.id._serialized);

      // Wait for chat to fully load
      await sleep(10000);

      // Retry fetch with rehydrated chat
      console.log(`[WhatsApp] Retrying fetch with rehydrated chat: ${chatName}`);
      const messages = await rehydratedChat.fetchMessages({ limit: 20 });
      return messages;
    } catch (retryErr) {
      console.error(
        `[WhatsApp] Retry fetch failed for "${chatName}": ${retryErr.message}`
      );
      throw retryErr;
    }
  }
}

// ============================================================================
// INITIAL FETCH (best-effort recovery for offline messages)
// ============================================================================

async function initialFetch() {
  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts) {
    try {
      attempts++;
      console.log(
        `[WhatsApp] Initial fetch attempt ${attempts}/${maxAttempts}...`
      );

      // Exponential backoff: 5s, 10s, 15s
      const backoffMs = 5000 * attempts;
      await sleep(backoffMs);

      // Get all chats (list view)
      const chats = await client.getChats();
      console.log(`[WhatsApp] Found ${chats.length} chats`);

      for (const chatName of targetChats) {
        try {
          // Find chat from list
          const chatFromList = chats.find((c) => c.name === chatName);
          if (!chatFromList) {
            console.log(`[WhatsApp] Chat not found: ${chatName}`);
            continue;
          }

          // CRITICAL: Rehydrate chat using getChatById
          console.log(
            `[WhatsApp] Rehydrating chat for initial fetch: ${chatName}`
          );
          const chat = await client.getChatById(chatFromList.id._serialized);

          // Wait for chat to fully load
          await sleep(10000);

          // Use safe fetch wrapper
          const messages = await safeFetchMessages(chat, chatName);

          // Process messages
          const since = lastFetchTime[chatName] || null;
          for (const msg of messages) {
            const hasText =
              typeof msg.body === "string" && msg.body.trim() !== "";
            if (!hasText) continue;
            if (since && msg.timestamp * 1000 <= since) continue;

            const msgId = msg.id._serialized;
            if (!processedMessageIds.has(msgId)) {
              processedMessageIds.add(msgId);
              await processMessage(msg, chatName);
            }
          }
        } catch (err) {
          console.warn(
            `[WhatsApp] Skipping initial fetch for "${chatName}": ${err.message}`
          );
          // Continue with next chat instead of failing
        }
      }

      console.log("[WhatsApp] Initial fetch complete");
      return; // Success - exit retry loop
    } catch (err) {
      console.warn(
        `[WhatsApp] Initial fetch attempt ${attempts} failed: ${err.message}`
      );
      if (attempts >= maxAttempts) {
        throw new Error(
          `Initial fetch failed after ${maxAttempts} attempts: ${err.message}`
        );
      }
    }
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

console.log("[WhatsApp] Initializing client...");
client.initialize();
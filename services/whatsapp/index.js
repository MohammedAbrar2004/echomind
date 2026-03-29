const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const { targetChats, pollIntervalMinutes, sessionPath } = require("./config");
const { sendMessages } = require("./sender");

// Tracks last fetch timestamp per chat
const lastFetchTime = {};

// Initialize WhatsApp client with persistent local session
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: sessionPath }),
  puppeteer: {
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    protocolTimeout: 60000,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--no-first-run", "--no-default-browser-check"],
  },
});

client.on("qr", (qr) => {
  console.log("[WhatsApp] Scan QR code to authenticate:");
  qrcode.generate(qr, { small: true });
});

client.on("ready", async () => {
  console.log("[WhatsApp] Client ready.");
  console.log(`[WhatsApp] Monitoring chats: ${targetChats.join(", ")}`);

  await fetchAndSend();
  setInterval(fetchAndSend, pollIntervalMinutes * 60 * 1000);
});

client.on("auth_failure", (msg) => {
  console.error(`[WhatsApp] Auth failed: ${msg}`);
});

client.on("disconnected", (reason) => {
  console.warn(`[WhatsApp] Disconnected: ${reason}`);
});

async function fetchAndSend() {
  console.log(`[WhatsApp] Starting fetch cycle — ${new Date().toISOString()}`);

  try {
    const chats = await client.getChats();

    for (const chat of chats) {
      if (!targetChats.includes(chat.name)) {
        continue;
      }

      try {
        const since = lastFetchTime[chat.name] || null;

        const messages = await chat.fetchMessages({ limit: 50 });

        const newMessages = messages.filter((msg) => {
          if (typeof msg.body !== "string" || msg.body.trim() === "") {
            return false;
          }
          if (since && msg.timestamp * 1000 <= since) {
            return false;
          }
          return true;
        });

        if (newMessages.length === 0) {
          console.log(`[WhatsApp] No new messages in: ${chat.name}`);
          continue;
        }

        const normalized = newMessages.map((msg) => ({
          chat_name: chat.name || chat.id._serialized,
          message_id: msg.id && msg.id._serialized ? msg.id._serialized : `${chat.id._serialized}-${msg.timestamp}`,
          timestamp: new Date(msg.timestamp * 1000).toISOString(),
          sender: msg._data.notifyName || msg.author || msg.from || "unknown",
          message: msg.body,
          is_group: chat.isGroup || false,
        }));

        await sendMessages(normalized);

        const latest = Math.max(...newMessages.map((m) => m.timestamp * 1000));
        lastFetchTime[chat.name] = latest;

        console.log(`[WhatsApp] Sent ${newMessages.length} messages from: ${chat.name}`);
      } catch (chatErr) {
        console.error(`[WhatsApp] Error processing chat "${chat.name}": ${chatErr.message}`);
      }
    }
  } catch (err) {
    console.error(`[WhatsApp] Fetch cycle failed: ${err.message}`);
  }
}

console.log("[WhatsApp] Initializing client...");
client.initialize();

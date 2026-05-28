/**
 * WhatsApp Bridge — the REAL platform integration. OWNER: Bridge owner (fullstack pair).
 *
 * Links our app as a WhatsApp "linked device" (parent scans a QR, exactly like
 * WhatsApp Web). Streams real incoming group messages to the backend as contract A
 * (IncomingMessage) -> POST /ingest. Drop-in replacement for simulator.py: same
 * contract, so the backend needs ZERO changes.
 *
 * Unofficial library (whatsapp-web.js). For the demo only, on a burner/demo number.
 * Run:
 *   npm install
 *   node index.js          # prints a QR in the terminal — scan it from the phone
 *                          # (WhatsApp > Settings > Linked devices > Link a device)
 */
const fs = require("fs");
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/ingest";
const GROUPS_ONLY = (process.env.GROUPS_ONLY || "true") === "true";
const CONTEXT_WINDOW = 2;

// We skip Puppeteer's bundled Chromium (flaky download) and drive a system browser.
// Override with CHROME_PATH; otherwise auto-detect Chrome/Edge on Windows.
function resolveBrowserPath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const candidates = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  ];
  return candidates.find((p) => fs.existsSync(p)); // undefined -> Puppeteer's own Chromium
}
const BROWSER_PATH = resolveBrowserPath();

// Rolling buffer of recent messages per chat, for context_before.
const recent = new Map(); // chatId -> [{sender_name, text}]

if (!BROWSER_PATH) {
  console.warn(
    "[bridge] No system Chrome/Edge found. Set CHROME_PATH=...chrome.exe, " +
      "or run `npm install` without PUPPETEER_SKIP_DOWNLOAD to fetch bundled Chromium."
  );
} else {
  console.log(`[bridge] using browser: ${BROWSER_PATH}`);
}

const client = new Client({
  authStrategy: new LocalAuth(), // persists session in .wwebjs_auth/ — scan once
  puppeteer: {
    executablePath: BROWSER_PATH, // undefined -> Puppeteer's bundled Chromium
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  },
});

client.on("qr", (qr) => {
  console.log("\n[bridge] Scan this QR from WhatsApp > Linked devices:\n");
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  const me = client.info?.wid?._serialized || "unknown";
  console.log(`[bridge] connected. child account = ${me}`);
});

// 'message_create' fires for BOTH incoming and the child's own outgoing messages,
// so we can flag the child as aggressor too (not only victim/bystander).
client.on("message_create", async (msg) => {
  try {
    const chat = await msg.getChat();
    if (GROUPS_ONLY && !chat.isGroup) return;

    const childId = client.info.wid._serialized;
    const senderId = msg.fromMe ? childId : msg.author || msg.from;
    const contact = await msg.getContact().catch(() => null);
    const senderName = msg.fromMe
      ? "הילד שלי"
      : (contact?.pushname || contact?.name || senderId);

    const chatId = chat.id._serialized;
    const before = (recent.get(chatId) || []).slice(-CONTEXT_WINDOW).map((m) => m.text);

    const payload = {
      message_id: msg.id._serialized,
      group_name: chat.name || "קבוצה",
      sender_id: senderId,
      sender_name: senderName,
      child_id: childId,
      text: msg.body || "",
      media_url: msg.hasMedia ? "[media]" : null, // TODO: download + analyze media
      timestamp: new Date(msg.timestamp * 1000).toISOString(),
      context_before: before,
      context_after: [], // future messages unknown at send time; left empty by design
    };

    await send(payload);

    const buf = recent.get(chatId) || [];
    buf.push({ sender_name: senderName, text: payload.text });
    recent.set(chatId, buf.slice(-10));
  } catch (err) {
    console.error("[bridge] handler error:", err.message);
  }
});

async function send(payload) {
  const label = `${payload.sender_name}: ${payload.text}`;
  try {
    const res = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log(`[${data.alert_created ? "🚨 ALERT" : "ok"}] ${label}`);
  } catch (err) {
    console.error(`[send failed] ${label} (${err.message})`);
  }
}

client.initialize();

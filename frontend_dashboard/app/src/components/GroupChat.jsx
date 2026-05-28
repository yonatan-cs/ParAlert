import { useEffect, useRef, useState } from "react";
import { useI18n } from "../i18n/I18nContext.jsx";

// A persistent, interactive WhatsApp-style group chat docked beside the dashboard.
// Each message you send is analyzed live by the backend (real ML when routed, else
// keyword). History is saved to localStorage like a real WhatsApp group. A toxic /
// disinformation message also pops as a live alert on the dashboard next to it.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const STORAGE_KEY = "safenet.groupchat";

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function clockTime(iso, locale) {
  try {
    return new Date(iso).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

const pct = (x) => Math.round((x || 0) * 100);

export default function GroupChat() {
  const { t, locale } = useI18n();
  const g = t.tryit;
  const [msgs, setMsgs] = useState(loadHistory);
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs));
  }, [msgs]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  async function send(presetText) {
    const body = (presetText ?? text).trim();
    if (busy || (!body && !file)) return;
    const id = Date.now();
    const sendFile = file;
    setMsgs((m) => [...m, { id, fromMe: true, text: body, fileName: sendFile?.name || null, ts: new Date().toISOString() }]);
    setText("");
    setFile(null);
    setBusy(true);
    try {
      let res;
      if (sendFile) {
        const fd = new FormData();
        fd.append("text", body);
        fd.append("file", sendFile);
        res = await fetch(`${API_BASE}/analyze/upload`, { method: "POST", body: fd });
      } else {
        res = await fetch(`${API_BASE}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: body, media_url: null }),
        });
      }
      if (!res.ok) throw new Error("bad status");
      const r = await res.json();
      setMsgs((m) => [...m, { id: id + 1, system: true, analysis: r, ts: new Date().toISOString() }]);
    } catch {
      setMsgs((m) => [...m, { id: id + 1, system: true, error: true, ts: new Date().toISOString() }]);
    } finally {
      setBusy(false);
    }
  }

  function clearChat() {
    setMsgs([]);
  }

  return (
    <div className="flex h-[72vh] flex-col overflow-hidden rounded-2xl border border-edge lg:h-[calc(100vh-3rem)]">
      {/* WhatsApp-style header */}
      <div className="flex items-center justify-between bg-[#075E54] px-4 py-3 text-white">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15 text-lg">🛡️</span>
          <div>
            <div className="font-semibold leading-tight">{g.groupName}</div>
            <div className="text-xs text-emerald-100/80">{g.members}</div>
          </div>
        </div>
        {msgs.length > 0 && (
          <button
            type="button"
            onClick={clearChat}
            title={g.clear}
            className="rounded-full bg-white/15 px-2.5 py-1 text-xs hover:bg-white/25"
          >
            🗑 {g.clear}
          </button>
        )}
      </div>

      {/* not-the-product disclaimer (always visible) */}
      <div className="bg-surface px-3 py-1 text-center text-[11px] text-faint">{g.disclaimer}</div>

      {/* chat body */}
      <div className="flex-1 space-y-2 overflow-y-auto bg-[#ECE5DD] p-3">
        {msgs.length === 0 && (
          <div className="mx-auto mt-6 max-w-[85%] rounded-xl bg-white/80 px-3 py-2 text-center text-xs text-slate-600">
            {g.welcome}
          </div>
        )}
        {msgs.map((m) =>
          m.system ? (
            <SystemBubble key={m.id} m={m} g={g} t={t} />
          ) : (
            <MyBubble key={m.id} m={m} g={g} locale={locale} />
          )
        )}
        {busy && (
          <div className="flex justify-start">
            <div className="rounded-lg rounded-tl-none bg-white px-3 py-2 text-sm text-slate-500 shadow-sm">
              {g.analyzing}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* sample chips + input */}
      <div className="space-y-2 border-t border-edge bg-surface p-2">
        <div className="flex flex-wrap gap-1.5">
          {g.samples.map((s) => (
            <button
              key={s.label}
              type="button"
              disabled={busy}
              onClick={() => send(s.text)}
              className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-muted transition-colors hover:bg-edge hover:text-content disabled:opacity-40"
            >
              {s.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <label
            title={g.attach}
            className={`flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full text-lg ${
              file ? "bg-accent/20 text-accent" : "bg-surface-2 text-muted hover:text-content"
            }`}
          >
            📎
            <input
              type="file"
              accept="image/*,video/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
            />
          </label>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={file ? `📎 ${file.name}` : g.placeholder}
            className="min-w-0 flex-1 rounded-full border border-edge bg-ink px-4 py-2 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30"
          />
          <button
            type="button"
            onClick={() => send()}
            disabled={busy || (!text.trim() && !file)}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent text-ink transition disabled:opacity-40"
            aria-label={g.send}
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}

function MyBubble({ m, g, locale }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] rounded-lg rounded-tr-none bg-[#DCF8C6] px-3 py-2 text-sm text-slate-800 shadow-sm">
        <div className="mb-0.5 text-[11px] font-semibold text-emerald-700">{g.you}</div>
        {m.fileName && (
          <div className="mb-1 rounded bg-black/5 px-2 py-1 text-xs text-slate-600">📎 {m.fileName}</div>
        )}
        {m.text && <span className="whitespace-pre-wrap break-words">{m.text}</span>}
        <div className="mt-0.5 text-end text-[10px] text-slate-500">{clockTime(m.ts, locale)}</div>
      </div>
    </div>
  );
}

function SystemBubble({ m, g, t }) {
  const r = m.analysis;
  const tone = m.error
    ? { text: "text-slate-600", icon: "⚠️", label: g.error }
    : r.is_toxic
      ? { text: "text-red-600", icon: "🛡️", label: g.verdictBullying }
      : r.alert_type === "disinformation" && r.credibility
        ? { text: "text-amber-600", icon: "📰", label: g.verdictDisinfo }
        : { text: "text-green-600", icon: "✓", label: g.verdictClean };
  const isDisinfo = !m.error && r.alert_type === "disinformation" && r.credibility;
  const realModel = !m.error && r.model_used && !r.model_used.includes("keyword") && r.model_used !== "stub";

  return (
    <div className="flex justify-start">
      <div className="max-w-[88%] space-y-1 rounded-lg rounded-tl-none bg-white px-3 py-2 text-sm text-slate-800 shadow-sm">
        <div className="text-[11px] font-semibold text-emerald-700">🛡️ SafeNet</div>
        <div className={`flex items-center gap-1.5 font-medium ${tone.text}`}>
          <span>{tone.icon}</span>
          {tone.label}
        </div>
        {!m.error && r.is_toxic && !isDisinfo && (
          <div className="text-xs text-slate-500">
            {g.toxicity} {pct(r.toxicity_score)}% · {t.category[r.category] || r.category}
          </div>
        )}
        {isDisinfo && (
          <div className="text-xs text-slate-500">
            {t.card.credibility} {pct(r.credibility.score)}% · {r.credibility.verdict}
          </div>
        )}
        {!m.error && r.media && (
          <div className="text-xs text-slate-500">
            {g.nsfw} {pct(r.media.safety_score)}% · {g.deepfake} {pct(r.media.ai_score)}%
          </div>
        )}
        {!m.error && (
          <div className="flex flex-wrap gap-1 text-[10px] text-slate-400">
            <span className={realModel ? "text-emerald-600" : ""}>
              {realModel ? g.realModelTag : g.keywordTag}
            </span>
            {r.alert_created && <span className="text-emerald-600">· {g.popped}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

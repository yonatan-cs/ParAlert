import { useEffect, useMemo, useRef, useState } from "react";
import AlertCard from "./components/AlertCard.jsx";
import SummaryBar from "./components/SummaryBar.jsx";
import FilterBar from "./components/FilterBar.jsx";
import ChatSimulator from "./components/ChatSimulator.jsx";
import Settings from "./components/Settings.jsx";

// Backend base is env-driven for deploy (Vercel sets VITE_API_BASE to the hosted
// backend). Defaults to local FS-A server. WS scheme derived: http->ws, https->wss.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const API = `${API_BASE}/alerts`;
const WS_URL = `${API_BASE.replace(/^http/, "ws")}/ws/alerts`;
const POLL_MS = 3000;

const TABS = [
  { key: "chat", label: "📱 צ'אט הילד" },
  { key: "dashboard", label: "🛡️ דשבורד" },
  { key: "settings", label: "⚙️ הגדרות" },
];

// Dashboard is grouped into sections; each alert lands in exactly one (severe first).
const SECTIONS = [
  { key: "severe", title: "🚨 מקרים חמורים — מומלץ לפנות למשטרה", match: (a) => a.escalation === "police" },
  { key: "bullying", title: "🛡️ בריונות", match: (a) => a.alert_type !== "disinformation" && a.escalation !== "police" },
  { key: "disinfo", title: "📰 דיסאינפורמציה", match: (a) => a.alert_type === "disinformation" },
];

export default function App() {
  const [alerts, setAlerts] = useState([]);
  const [source, setSource] = useState("טוען…");
  const [live, setLive] = useState(false);
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState("dashboard");
  const seen = useRef(new Set()); // alert_ids already shown — for the "new" highlight

  useEffect(() => {
    let active = true;

    async function load() {
      let data = null;
      let connected = false;
      try {
        const r = await fetch(API);
        if (!r.ok) throw new Error(`status ${r.status}`);
        data = await r.json();
        // Treat backend as "live" only if it actually has alerts. An empty
        // backend (e.g. Render reset, not re-seeded) falls back to the rich
        // mock so the demo dashboard is never empty.
        connected = Array.isArray(data) && data.length > 0;
      } catch {
        connected = false;
      }
      if (!connected) {
        try {
          const r = await fetch("/mock_data.json");
          data = await r.json();
        } catch {
          if (active) setSource("שגיאה בטעינה");
          return;
        }
      }
      if (!active || !Array.isArray(data)) return;
      setLive(connected);
      setSource(connected ? "מחובר · זמן אמת" : "מצב הדגמה");
      setAlerts(data);
    }

    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  // Real-time push (FS-A's WebSocket) with auto-reconnect + heartbeat. Polling above
  // stays the safety net, so a dropped socket (e.g. a Render free-tier cold start)
  // degrades gracefully and then transparently re-subscribes with backoff.
  useEffect(() => {
    let ws;
    let retry = 0;
    let reconnectTimer;
    let stopped = false;

    function scheduleReconnect() {
      const delay = Math.min(1000 * 2 ** retry, 15000); // exponential backoff, cap 15s
      retry += 1;
      reconnectTimer = setTimeout(connect, delay);
    }

    function connect() {
      if (stopped) return;
      try {
        ws = new WebSocket(WS_URL);
      } catch {
        scheduleReconnect();
        return;
      }
      ws.onopen = () => {
        retry = 0;
        setLive(true);
        setSource("מחובר · זמן אמת");
      };
      ws.onmessage = (ev) => {
        let msg;
        try {
          msg = JSON.parse(ev.data);
        } catch {
          return;
        }
        if (!msg) return;
        if (msg.type === "ping") {
          setLive(true); // heartbeat — keep the indicator green between alerts
          return;
        }
        if (!msg.alert_id) return;
        setAlerts((prev) =>
          prev.some((a) => a.alert_id === msg.alert_id) ? prev : [msg, ...prev]
        );
        setLive(true);
        setSource("מחובר · זמן אמת");
      };
      ws.onclose = () => {
        if (!stopped) scheduleReconnect();
      };
      ws.onerror = () => {
        try {
          ws.close(); // onclose will schedule the reconnect
        } catch {
          /* already closed */
        }
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(reconnectTimer);
      try {
        ws && ws.close();
      } catch {
        /* already closed */
      }
    };
  }, []);

  const visible = useMemo(() => {
    const sorted = [...alerts].sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
    return filter === "all" ? sorted : sorted.filter((a) => a.role_of_child === filter);
  }, [alerts, filter]);

  const isNew = (id) => {
    if (seen.current.has(id)) return false;
    seen.current.add(id);
    return true;
  };

  return (
    <div className="mx-auto min-h-screen max-w-2xl px-4 py-6 md:px-6">
      <header className="mb-5 flex items-center gap-3">
        <h1 className="text-xl font-bold tracking-tight">🛡️ SafeNet</h1>
        {view === "dashboard" && (
          <span className="flex items-center gap-1.5 rounded-full bg-surface px-3 py-1 text-xs text-muted">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${live ? "bg-sev-low animate-pulse-live" : "bg-sev-medium"}`}
            />
            {source}
          </span>
        )}
      </header>

      <nav className="mb-5 grid grid-cols-3 gap-1 rounded-xl bg-surface p-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setView(t.key)}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150 ${
              view === t.key ? "bg-content text-ink" : "text-muted hover:text-content"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div key={view} className="animate-fade">
        {view === "chat" && <ChatSimulator />}
        {view === "settings" && <Settings />}
        {view === "dashboard" && (
          <>
            <SummaryBar alerts={alerts} />
            <FilterBar value={filter} onChange={setFilter} alerts={alerts} />
            {visible.length === 0 ? (
              <div className="py-16 text-center text-faint">
                {alerts.length === 0 ? "אין התראות 🎉" : "אין התראות בקטגוריה זו"}
              </div>
            ) : (
              SECTIONS.map((s) => {
                const items = visible.filter(s.match);
                if (!items.length) return null;
                return (
                  <section key={s.key} className="mb-6">
                    <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-muted">
                      {s.title}
                      <span className="rounded-full bg-surface-2 px-2 py-0.5 text-[11px] text-faint">
                        {items.length}
                      </span>
                    </h2>
                    {items.map((a) => (
                      <AlertCard key={a.alert_id} alert={a} isNew={isNew(a.alert_id)} />
                    ))}
                  </section>
                );
              })
            )}
          </>
        )}
      </div>
    </div>
  );
}

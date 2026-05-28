import { useEffect, useMemo, useRef, useState } from "react";
import AlertCard from "./components/AlertCard.jsx";
import SummaryBar from "./components/SummaryBar.jsx";
import FilterBar from "./components/FilterBar.jsx";
import ChatSimulator from "./components/ChatSimulator.jsx";
import Settings from "./components/Settings.jsx";

const API = "http://localhost:8000/alerts";
const WS_URL = "ws://localhost:8000/ws/alerts"; // FS-A real-time push; polling stays as fallback
const POLL_MS = 3000;

const TABS = [
  { key: "chat", label: "📱 צ'אט הילד" },
  { key: "dashboard", label: "🛡️ דשבורד" },
  { key: "settings", label: "⚙️ הגדרות" },
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
        connected = true;
      } catch {
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
      setSource(connected ? "מחובר" : "מצב הדגמה");
      setAlerts(data);
    }

    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  // Real-time push (FS-A's WebSocket). Enhancement only — polling above is the
  // safety net, so a missing/closed socket degrades gracefully.
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(WS_URL);
    } catch {
      return;
    }
    ws.onmessage = (ev) => {
      let alert;
      try {
        alert = JSON.parse(ev.data);
      } catch {
        return;
      }
      if (!alert || !alert.alert_id) return;
      setAlerts((prev) =>
        prev.some((a) => a.alert_id === alert.alert_id) ? prev : [alert, ...prev]
      );
      setLive(true);
      setSource("מחובר · זמן אמת");
    };
    return () => {
      try {
        ws.close();
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
              className={`inline-block h-1.5 w-1.5 rounded-full ${live ? "bg-sev-low" : "bg-sev-medium"}`}
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
              visible.map((a) => (
                <AlertCard key={a.alert_id} alert={a} isNew={isNew(a.alert_id)} />
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
}

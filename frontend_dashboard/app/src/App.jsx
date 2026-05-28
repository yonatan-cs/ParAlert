import { useEffect, useMemo, useRef, useState } from "react";
import AlertCard from "./components/AlertCard.jsx";
import SummaryBar from "./components/SummaryBar.jsx";
import FilterBar from "./components/FilterBar.jsx";
import ChatSimulator from "./components/ChatSimulator.jsx";

const API = "http://localhost:8000/alerts";
const POLL_MS = 3000;

export default function App() {
  const [alerts, setAlerts] = useState([]);
  const [source, setSource] = useState("טוען…");
  const [live, setLive] = useState(false);
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState("dashboard"); // "dashboard" | "chat"
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
      setSource(connected ? "מחובר ל-API" : "נתוני MOCK (אין חיבור לשרת)");
      setAlerts(data);
    }

    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  // Newest first; filter by the child's role (the 3 angles).
  const visible = useMemo(() => {
    const sorted = [...alerts].sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
    return filter === "all"
      ? sorted
      : sorted.filter((a) => a.role_of_child === filter);
  }, [alerts, filter]);

  const isNew = (id) => {
    if (seen.current.has(id)) return false;
    seen.current.add(id);
    return true;
  };

  return (
    <div className="mx-auto min-h-screen max-w-3xl px-4 py-6 md:px-8">
      <header className="mb-5 flex items-center gap-3">
        <h1 className="text-2xl font-bold">🛡️ SafeNet</h1>
        {view === "dashboard" && (
          <span className="flex items-center gap-1.5 rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
            <span
              className={`inline-block h-2 w-2 rounded-full ${live ? "bg-green-400" : "bg-amber-400"}`}
            />
            {source}
          </span>
        )}
      </header>

      <div className="mb-5 flex gap-1 rounded-xl bg-slate-800 p-1">
        <TabButton active={view === "chat"} onClick={() => setView("chat")}>
          📱 צ'אט הילד
        </TabButton>
        <TabButton active={view === "dashboard"} onClick={() => setView("dashboard")}>
          🛡️ דשבורד הורה
        </TabButton>
      </div>

      {view === "chat" ? (
        <ChatSimulator />
      ) : (
        <>
          <SummaryBar alerts={alerts} />
          <FilterBar value={filter} onChange={setFilter} />
          {visible.length === 0 ? (
            <div className="py-16 text-center text-slate-500">
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
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition ${
        active ? "bg-slate-200 text-slate-900" : "text-slate-300 hover:bg-slate-700"
      }`}
    >
      {children}
    </button>
  );
}

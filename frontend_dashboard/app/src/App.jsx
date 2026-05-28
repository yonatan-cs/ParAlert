import { useEffect, useRef, useState } from "react";
import AlertCard from "./components/AlertCard.jsx";

const API = "http://localhost:8000/alerts";
const POLL_MS = 3000;

export default function App() {
  const [alerts, setAlerts] = useState([]);
  const [source, setSource] = useState("טוען…");
  const [live, setLive] = useState(false);
  const seen = useRef(new Set()); // alert_ids already shown — for "new" highlight

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

  // Mark which alerts are new this render (for entrance animation).
  const isNew = (id) => {
    if (seen.current.has(id)) return false;
    seen.current.add(id);
    return true;
  };

  return (
    <div className="min-h-screen mx-auto max-w-3xl px-4 py-6 md:px-8">
      <header className="mb-6 flex items-center gap-3">
        <h1 className="text-2xl font-bold">🛡️ SafeNet</h1>
        <span className="flex items-center gap-1.5 rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
          <span
            className={`inline-block h-2 w-2 rounded-full ${live ? "bg-green-400" : "bg-amber-400"}`}
          />
          {source}
        </span>
      </header>

      {alerts.length === 0 ? (
        <div className="py-16 text-center text-slate-500">אין התראות 🎉</div>
      ) : (
        alerts.map((a) => <AlertCard key={a.alert_id} alert={a} isNew={isNew(a.alert_id)} />)
      )}
    </div>
  );
}

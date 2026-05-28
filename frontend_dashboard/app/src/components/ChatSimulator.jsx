import { useEffect, useRef, useState } from "react";
import { DEMO_GROUP, DEMO_CHAT } from "../data/demoChat.js";

// WhatsApp-style group chat that plays a scripted escalation — the demo opener.
// Pure frontend, no backend. When a toxic message lands, a SafeNet banner flashes.
export default function ChatSimulator() {
  const [shown, setShown] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [flash, setFlash] = useState(false);
  const timers = useRef([]);
  const bottomRef = useRef(null);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [shown]);

  function clearTimers() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }

  function reset() {
    clearTimers();
    setShown(0);
    setPlaying(false);
    setFlash(false);
  }

  function play() {
    clearTimers();
    setShown(0);
    setFlash(false);
    setPlaying(true);
    let acc = 0;
    DEMO_CHAT.forEach((m, i) => {
      acc += m.delayMs;
      timers.current.push(
        setTimeout(() => {
          setShown(i + 1);
          if (m.toxic) {
            setFlash(true);
            timers.current.push(setTimeout(() => setFlash(false), 2600));
          }
          if (i === DEMO_CHAT.length - 1) setPlaying(false);
        }, acc)
      );
    });
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-700">
      <div className="flex items-center justify-between bg-[#075E54] px-4 py-3 text-white">
        <div>
          <div className="font-semibold">{DEMO_GROUP}</div>
          <div className="text-xs text-emerald-100/80">4 משתתפים</div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={play}
            disabled={playing}
            className="rounded-full bg-white/15 px-3 py-1 text-sm hover:bg-white/25 disabled:opacity-50"
          >
            ▶ הפעל
          </button>
          <button
            type="button"
            onClick={reset}
            className="rounded-full bg-white/15 px-3 py-1 text-sm hover:bg-white/25"
          >
            ↺
          </button>
        </div>
      </div>

      <div className="relative h-[420px] space-y-2 overflow-y-auto bg-[#ECE5DD] p-3">
        {flash && (
          <div className="animate-enter sticky top-0 z-10 mx-auto w-fit rounded-full bg-sev-high px-4 py-1.5 text-sm font-medium text-white shadow-lg">
            🛡️ SafeNet זיהה בעיה — התראה נשלחה להורה
          </div>
        )}

        {shown === 0 ? (
          <div className="flex h-full items-center justify-center text-slate-500">
            לחץ ▶ כדי להריץ שיחת דמו
          </div>
        ) : (
          DEMO_CHAT.slice(0, shown).map((m, i) => (
            <div key={i} className={`animate-msg flex ${m.fromChild ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[78%] rounded-lg px-3 py-1.5 text-sm shadow-sm ${
                  m.fromChild ? "bg-[#DCF8C6] text-slate-800" : "bg-white text-slate-800"
                }`}
              >
                {!m.fromChild && (
                  <div className="text-[11px] font-semibold text-emerald-700">{m.sender}</div>
                )}
                {m.text}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

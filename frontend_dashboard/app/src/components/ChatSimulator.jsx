import { useEffect, useRef, useState } from "react";
import { DEMO_SCENARIOS } from "../data/demoChat.js";

// WhatsApp-style chat opener with a group switcher. Plays the selected group's
// scripted conversation; flagged messages flash a typed SafeNet banner and media
// renders as image/video (censored for sensitive content). Pure frontend.
const FLASH = {
  severe: { text: "🚨 מקרה חמור — מומלץ לפנות למשטרה (100)", cls: "bg-sev-high" },
  disinfo: { text: "📰 SafeNet זיהה דיסאינפורמציה — התראה נשלחה", cls: "bg-amber-600" },
  toxic: { text: "🛡️ SafeNet זיהה בריונות — התראה נשלחה להורה", cls: "bg-sev-high" },
};

function flagType(m) {
  if (m.severe) return "severe";
  if (m.disinfo) return "disinfo";
  if (m.toxic) return "toxic";
  return null;
}

function Media({ m }) {
  const [revealed, setRevealed] = useState(false);
  if (!m.media) return null;
  const isVideo = m.media === "video";
  const url = m.mediaUrl || "https://picsum.photos/seed/safenet/480/300";
  const blurred = m.severe && m.media === "image" && !revealed;
  return (
    <div className="relative mt-1 max-w-[220px] overflow-hidden rounded-md">
      <img
        src={url}
        alt=""
        loading="lazy"
        className={`max-h-44 w-full object-cover ${blurred ? "scale-110 blur-2xl" : ""}`}
      />
      {isVideo && !blurred && (
        <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-3xl text-white/90">
          ▶
        </span>
      )}
      {blurred && (
        <button
          type="button"
          onClick={() => setRevealed(true)}
          className="absolute inset-0 flex flex-col items-center justify-center gap-0.5 bg-black/35 text-[11px] font-medium text-white"
        >
          <span>תמונה רגישה</span>
          <span className="underline">הצג</span>
        </button>
      )}
    </div>
  );
}

export default function ChatSimulator() {
  const [idx, setIdx] = useState(0);
  const [shown, setShown] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [flash, setFlash] = useState(null);
  const timers = useRef([]);
  const bottomRef = useRef(null);

  const scenario = DEMO_SCENARIOS[idx];

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
    setFlash(null);
  }

  function selectGroup(i) {
    reset();
    setIdx(i);
  }

  function play() {
    clearTimers();
    setShown(0);
    setFlash(null);
    setPlaying(true);
    let acc = 0;
    scenario.messages.forEach((m, i) => {
      acc += m.delayMs;
      timers.current.push(
        setTimeout(() => {
          setShown(i + 1);
          const t = flagType(m);
          if (t) {
            setFlash(t);
            timers.current.push(setTimeout(() => setFlash(null), 2800));
          }
          if (i === scenario.messages.length - 1) setPlaying(false);
        }, acc)
      );
    });
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-edge">
      {/* group switcher */}
      <div className="flex gap-1 overflow-x-auto bg-surface p-2">
        {DEMO_SCENARIOS.map((s, i) => (
          <button
            key={s.group}
            type="button"
            onClick={() => selectGroup(i)}
            className={`shrink-0 rounded-lg px-2.5 py-1 text-xs transition-colors duration-150 ${
              i === idx ? "bg-content text-ink" : "bg-surface-2 text-muted hover:text-content"
            }`}
          >
            {s.group}
          </button>
        ))}
      </div>

      {/* WhatsApp-style header */}
      <div className="flex items-center justify-between bg-[#075E54] px-4 py-3 text-white">
        <div>
          <div className="font-semibold">{scenario.group}</div>
          <div className="text-xs text-emerald-100/80">{scenario.members}</div>
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

      {/* chat body */}
      <div className="relative h-[420px] space-y-2 overflow-y-auto bg-[#ECE5DD] p-3">
        {flash && (
          <div
            className={`animate-enter sticky top-0 z-10 mx-auto w-fit rounded-full px-4 py-1.5 text-sm font-medium text-white shadow-lg ${FLASH[flash].cls}`}
          >
            {FLASH[flash].text}
          </div>
        )}

        {shown === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-slate-500">
            בחר קבוצה ולחץ ▶ כדי להריץ שיחת דמו
          </div>
        ) : (
          scenario.messages.slice(0, shown).map((m, i) => (
            <div key={i} className={`animate-msg flex ${m.fromChild ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-lg px-3 py-1.5 text-sm shadow-sm ${
                  m.fromChild ? "bg-[#DCF8C6] text-slate-800" : "bg-white text-slate-800"
                }`}
              >
                {!m.fromChild && (
                  <div className="text-[11px] font-semibold text-emerald-700">{m.sender}</div>
                )}
                {m.text}
                <Media m={m} />
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

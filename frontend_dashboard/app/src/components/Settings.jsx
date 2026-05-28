import { useEffect, useState } from "react";

const STORAGE_KEY = "safenet.settings";

const DEFAULTS = {
  childName: "יונתן",
  childAge: 12,
  sensitivity: "medium",
  notify: { push: true, email: false, quietHours: true },
  groups: [
    { id: "g1", name: "כיתה ו'2 - בלי המורה", on: true },
    { id: "g2", name: "חברים מהשכונה", on: true },
    { id: "g3", name: "כדורגל שכבה ו'", on: false },
  ],
};

function loadSettings() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") };
  } catch {
    return DEFAULTS;
  }
}

const SENSITIVITY = [
  { key: "low", label: "נמוך", hint: "רק חמור" },
  { key: "medium", label: "בינוני", hint: "מאוזן" },
  { key: "high", label: "גבוה", hint: "גם רמזים" },
];

export default function Settings() {
  const [s, setS] = useState(loadSettings);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  }, [s]);

  const set = (patch) => setS((prev) => ({ ...prev, ...patch }));
  const setNotify = (k, v) => setS((prev) => ({ ...prev, notify: { ...prev.notify, [k]: v } }));
  const toggleGroup = (id) =>
    setS((prev) => ({
      ...prev,
      groups: prev.groups.map((g) => (g.id === id ? { ...g, on: !g.on } : g)),
    }));

  return (
    <div className="animate-fade">
      <Section title="פרופיל הילד">
        <div className="flex items-center gap-3 px-4 py-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent/15 text-lg font-bold text-accent">
            {(s.childName || "?").trim().charAt(0)}
          </div>
          <div className="flex flex-1 gap-2">
            <Field label="שם">
              <input
                value={s.childName}
                onChange={(e) => set({ childName: e.target.value })}
                className="w-full rounded-lg border border-edge bg-ink px-3 py-1.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30"
              />
            </Field>
            <Field label="גיל">
              <input
                type="number"
                min="5"
                max="18"
                value={s.childAge}
                onChange={(e) => set({ childAge: Number(e.target.value) })}
                className="w-20 rounded-lg border border-edge bg-ink px-3 py-1.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30"
              />
            </Field>
          </div>
        </div>
      </Section>

      <Section title="רגישות ההתראות" desc="כמה מוקדם להתריע. בינוני מומלץ לרוב המשפחות.">
        <div className="p-3">
          <div className="grid grid-cols-3 gap-1 rounded-xl bg-ink p-1">
            {SENSITIVITY.map((opt) => {
              const active = s.sensitivity === opt.key;
              return (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => set({ sensitivity: opt.key })}
                  className={`rounded-lg px-2 py-2 text-center transition-colors duration-150 ${
                    active ? "bg-surface-2 text-content" : "text-muted hover:text-content"
                  }`}
                >
                  <div className="text-sm font-medium">{opt.label}</div>
                  <div className="text-[11px] text-faint">{opt.hint}</div>
                </button>
              );
            })}
          </div>
        </div>
      </Section>

      <Section title="התראות">
        <Row label="התראת פוש" hint="הודעה מיידית לטלפון">
          <Toggle checked={s.notify.push} onChange={(v) => setNotify("push", v)} />
        </Row>
        <Row label="סיכום במייל" hint="דוח יומי מרוכז">
          <Toggle checked={s.notify.email} onChange={(v) => setNotify("email", v)} />
        </Row>
        <Row label="שעות שקט" hint="ללא התראות 22:00–07:00 (אלא אם חמור)">
          <Toggle checked={s.notify.quietHours} onChange={(v) => setNotify("quietHours", v)} />
        </Row>
      </Section>

      <Section title="קבוצות במעקב" desc="בחר אילו קבוצות וואטסאפ לנטר.">
        {s.groups.map((g) => (
          <Row key={g.id} label={g.name}>
            <Toggle checked={g.on} onChange={() => toggleGroup(g.id)} />
          </Row>
        ))}
      </Section>

      <p className="px-1 pb-2 text-center text-xs text-faint">השינויים נשמרים אוטומטית</p>
    </div>
  );
}

function Section({ title, desc, children }) {
  return (
    <section className="mb-6">
      <h2 className="mb-1 text-sm font-semibold">{title}</h2>
      {desc && <p className="mb-2 text-xs text-faint">{desc}</p>}
      <div className="divide-y divide-edge overflow-hidden rounded-2xl border border-edge bg-surface">
        {children}
      </div>
    </section>
  );
}

function Row({ label, hint, children }) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3">
      <div className="min-w-0">
        <div className="truncate text-sm">{label}</div>
        {hint && <div className="text-xs text-faint">{hint}</div>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="flex-1">
      <span className="mb-1 block text-[11px] text-faint">{label}</span>
      {children}
    </label>
  );
}

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      dir="ltr"
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition-colors duration-200 ${
        checked ? "bg-accent" : "bg-surface-2"
      }`}
    >
      <span
        className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-content shadow transition-transform duration-200 ${
          checked ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  );
}

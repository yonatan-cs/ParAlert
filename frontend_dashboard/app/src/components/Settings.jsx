import { useEffect, useState } from "react";
import { useI18n } from "../i18n/I18nContext.jsx";

const STORAGE_KEY = "safenet.settings";

function defaultsFor(t) {
  return {
    childName: t.settings.defaultChild,
    childAge: 12,
    sensitivity: "medium",
    notify: { push: true, email: false, quietHours: true },
    groups: t.settings.defaultGroups.map((name, i) => ({ id: `g${i + 1}`, name, on: i !== 2 })),
    _touched: false,
  };
}

function loadSettings(t) {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (stored && stored._touched) return { ...defaultsFor(t), ...stored };
  } catch {
    /* ignore */
  }
  return defaultsFor(t);
}

const SENS = [
  { key: "low", label: "sensLow", hint: "sensLowHint" },
  { key: "medium", label: "sensMedium", hint: "sensMediumHint" },
  { key: "high", label: "sensHigh", hint: "sensHighHint" },
];

export default function Settings() {
  const { t, lang } = useI18n();
  const [s, setS] = useState(() => loadSettings(t));

  // Untouched settings follow the active language (clean fresh demo); once the
  // parent edits anything, their data is kept and persisted across reloads.
  useEffect(() => {
    setS((prev) => (prev._touched ? prev : defaultsFor(t)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  useEffect(() => {
    if (s._touched) localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  }, [s]);

  const set = (patch) => setS((prev) => ({ ...prev, ...patch, _touched: true }));
  const setNotify = (k, v) =>
    setS((prev) => ({ ...prev, notify: { ...prev.notify, [k]: v }, _touched: true }));
  const toggleGroup = (id) =>
    setS((prev) => ({
      ...prev,
      _touched: true,
      groups: prev.groups.map((g) => (g.id === id ? { ...g, on: !g.on } : g)),
    }));

  return (
    <div className="animate-fade">
      <Section title={t.settings.profile}>
        <div className="flex items-center gap-3 px-4 py-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent/15 text-lg font-bold text-accent">
            {(s.childName || "?").trim().charAt(0)}
          </div>
          <div className="flex flex-1 gap-2">
            <Field label={t.settings.name}>
              <input
                value={s.childName}
                onChange={(e) => set({ childName: e.target.value })}
                className="w-full rounded-lg border border-edge bg-ink px-3 py-1.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30"
              />
            </Field>
            <Field label={t.settings.age}>
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

      <Section title={t.settings.sensitivity} desc={t.settings.sensitivityDesc}>
        <div className="p-3">
          <div className="grid grid-cols-3 gap-1 rounded-xl bg-ink p-1">
            {SENS.map((opt) => {
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
                  <div className="text-sm font-medium">{t.settings[opt.label]}</div>
                  <div className="text-[11px] text-faint">{t.settings[opt.hint]}</div>
                </button>
              );
            })}
          </div>
        </div>
      </Section>

      <Section title={t.settings.notifications}>
        <Row label={t.settings.push} hint={t.settings.pushHint}>
          <Toggle checked={s.notify.push} onChange={(v) => setNotify("push", v)} />
        </Row>
        <Row label={t.settings.email} hint={t.settings.emailHint}>
          <Toggle checked={s.notify.email} onChange={(v) => setNotify("email", v)} />
        </Row>
        <Row label={t.settings.quiet} hint={t.settings.quietHint}>
          <Toggle checked={s.notify.quietHours} onChange={(v) => setNotify("quietHours", v)} />
        </Row>
      </Section>

      <Section title={t.settings.groups} desc={t.settings.groupsDesc}>
        {s.groups.map((g) => (
          <Row key={g.id} label={g.name}>
            <Toggle checked={g.on} onChange={() => toggleGroup(g.id)} />
          </Row>
        ))}
      </Section>

      <p className="px-1 pb-2 text-center text-xs text-faint">{t.settings.autosave}</p>
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

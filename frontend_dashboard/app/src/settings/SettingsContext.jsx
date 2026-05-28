import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useI18n } from "../i18n/I18nContext.jsx";

// Shared, persisted parent settings. Both the dashboard (App) and the Settings tab
// read/write here, so toggling a setting actually changes what the dashboard shows.
const STORAGE_KEY = "safenet.settings";
const SettingsContext = createContext(null);

export const SEVERITY_RANK = { high: 3, medium: 2, low: 1 };
// Sensitivity -> minimum severity rank shown. low = severe only; high = everything.
export const SENSITIVITY_MIN = { low: 3, medium: 2, high: 1 };

export function isQuietNow() {
  const h = new Date().getHours();
  return h >= 22 || h < 7; // 22:00–07:00
}

function load(defaults) {
  try {
    const s = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (s && typeof s === "object" && s._touched) {
      return {
        childName: s.childName ?? defaults.childName,
        childAge: s.childAge ?? defaults.childAge,
        sensitivity: s.sensitivity ?? defaults.sensitivity,
        notify: { ...defaults.notify, ...(s.notify || {}) },
        disabledGroups: Array.isArray(s.disabledGroups) ? s.disabledGroups : [],
        _touched: true,
      };
    }
  } catch {
    /* ignore */
  }
  return { ...defaults, disabledGroups: [], _touched: false };
}

export function SettingsProvider({ children }) {
  const { t } = useI18n();
  const defaults = {
    childName: t.settings.defaultChild,
    childAge: 12,
    sensitivity: "medium",
    notify: { push: true, email: false, quietHours: true },
  };
  const [settings, setSettings] = useState(() => load(defaults));
  const [availableGroups, setAvailableGroupsState] = useState([]);

  // Untouched child name follows the active language (clean fresh demo).
  useEffect(() => {
    setSettings((p) => (p._touched ? p : { ...p, childName: t.settings.defaultChild }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t]);

  useEffect(() => {
    if (settings._touched) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      } catch {
        /* ignore */
      }
    }
  }, [settings]);

  const update = useCallback((patch) => setSettings((p) => ({ ...p, ...patch, _touched: true })), []);
  const setNotify = useCallback(
    (key, val) => setSettings((p) => ({ ...p, notify: { ...p.notify, [key]: val }, _touched: true })),
    []
  );
  const toggleGroup = useCallback(
    (name) =>
      setSettings((p) => {
        const off = new Set(p.disabledGroups);
        if (off.has(name)) off.delete(name);
        else off.add(name);
        return { ...p, disabledGroups: [...off], _touched: true };
      }),
    []
  );

  // App registers the groups currently present in the alerts; skip no-op updates so
  // the 3s poll doesn't churn re-renders.
  const setAvailableGroups = useCallback((names) => {
    const next = [...new Set(names)].sort();
    setAvailableGroupsState((prev) =>
      prev.length === next.length && prev.every((g, i) => g === next[i]) ? prev : next
    );
  }, []);

  const value = useMemo(
    () => ({ settings, update, setNotify, toggleGroup, availableGroups, setAvailableGroups }),
    [settings, update, setNotify, toggleGroup, availableGroups, setAvailableGroups]
  );
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within <SettingsProvider>");
  return ctx;
}

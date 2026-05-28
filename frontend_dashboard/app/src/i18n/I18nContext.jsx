import { createContext, useContext, useEffect, useState } from "react";
import { STRINGS } from "./translations.js";

// Lightweight, dependency-free i18n. `lang` drives both the string table and the
// document direction (he -> rtl, en -> ltr). Choice persists in localStorage.
const STORAGE_KEY = "safenet.lang";
const I18nContext = createContext(null);

function initialLang() {
  try {
    // ?lang=en wins (shareable English link for an English-speaking judge),
    // then the saved choice, else Hebrew-first.
    const q = new URLSearchParams(window.location.search).get("lang");
    if (q === "he" || q === "en") return q;
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "he" || saved === "en") return saved;
  } catch {
    /* unavailable */
  }
  return "he";
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(initialLang);
  const dir = lang === "he" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    document.title = STRINGS[lang].title;
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      /* ignore */
    }
  }, [lang, dir]);

  const setLang = (l) => setLangState(l === "en" ? "en" : "he");

  const value = {
    lang,
    setLang,
    dir,
    t: STRINGS[lang],
    locale: lang === "he" ? "he-IL" : "en-US",
  };
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within <I18nProvider>");
  return ctx;
}

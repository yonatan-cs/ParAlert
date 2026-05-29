import { createContext, useContext, useEffect, useState } from "react";

// Dependency-free light/dark theme. `theme` drives documentElement[data-theme],
// which flips the semantic CSS tokens in index.css. Dark is the default identity;
// the choice persists in localStorage and is applied pre-paint by index.html.
const STORAGE_KEY = "paralert.theme";
const ThemeContext = createContext(null);

function initialTheme() {
  try {
    // ?theme= wins (shareable link), then the saved choice, else dark.
    const q = new URLSearchParams(window.location.search).get("theme");
    if (q === "light" || q === "dark") return q;
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* unavailable */
  }
  return "dark";
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  const setTheme = (t) => setThemeState(t === "light" ? "light" : "dark");
  const toggleTheme = () => setThemeState((t) => (t === "light" ? "dark" : "light"));

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within <ThemeProvider>");
  return ctx;
}

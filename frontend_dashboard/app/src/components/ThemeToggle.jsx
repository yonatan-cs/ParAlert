import { useTheme } from "../theme/ThemeContext.jsx";

// Compact light/dark segmented switch — same visual language as LanguageToggle.
// dir="ltr" keeps the order stable in both RTL and LTR layouts.
const OPTIONS = [
  ["light", "☀"],
  ["dark", "☾"],
];

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <div dir="ltr" className="flex items-center gap-0.5 rounded-md bg-surface p-0.5 text-sm">
      {OPTIONS.map(([code, glyph]) => (
        <button
          key={code}
          type="button"
          aria-pressed={theme === code}
          aria-label={code === "light" ? "Light theme" : "Dark theme"}
          onClick={() => setTheme(code)}
          className={`flex h-6 w-6 items-center justify-center rounded leading-none transition-colors duration-150 ${
            theme === code ? "bg-content text-ink" : "text-muted hover:text-content"
          }`}
        >
          {glyph}
        </button>
      ))}
    </div>
  );
}

import { useI18n } from "../i18n/I18nContext.jsx";

// Compact EN / עב segmented switch. dir="ltr" so the order is stable in both layouts.
const OPTIONS = [
  ["he", "עב"],
  ["en", "EN"],
];

export default function LanguageToggle() {
  const { lang, setLang } = useI18n();
  return (
    <div dir="ltr" className="flex items-center gap-0.5 rounded-md bg-surface p-0.5 text-xs">
      {OPTIONS.map(([code, label]) => (
        <button
          key={code}
          type="button"
          aria-pressed={lang === code}
          onClick={() => setLang(code)}
          className={`rounded px-2 py-0.5 transition-colors duration-150 ${
            lang === code ? "bg-content font-semibold text-ink" : "text-muted hover:text-content"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

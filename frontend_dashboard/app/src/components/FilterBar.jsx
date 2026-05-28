import { useI18n } from "../i18n/I18nContext.jsx";

const FILTER_KEYS = ["all", "victim", "aggressor", "bystander", "exposed"];

export default function FilterBar({ value, onChange, alerts }) {
  const { t } = useI18n();
  const countFor = (key) =>
    key === "all" ? alerts.length : alerts.filter((a) => a.role_of_child === key).length;

  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {FILTER_KEYS.map((key) => {
        const active = value === key;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onChange(key)}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-sm transition-colors duration-150 ${
              active
                ? "bg-content text-ink"
                : "bg-surface-2 text-muted hover:bg-edge hover:text-content"
            }`}
          >
            {t.filters[key]}
            <span
              className={`min-w-4 rounded-full px-1 text-center text-[11px] ${
                active ? "bg-ink/10 text-ink" : "bg-ink/40 text-faint"
              }`}
            >
              {countFor(key)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

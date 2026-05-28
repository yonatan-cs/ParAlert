const FILTERS = [
  { key: "all", label: "הכל" },
  { key: "victim", label: "קורבן" },
  { key: "aggressor", label: "תוקף" },
  { key: "bystander", label: "צופה" },
];

export default function FilterBar({ value, onChange, alerts }) {
  const countFor = (key) =>
    key === "all" ? alerts.length : alerts.filter((a) => a.role_of_child === key).length;

  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {FILTERS.map((f) => {
        const active = value === f.key;
        return (
          <button
            key={f.key}
            type="button"
            onClick={() => onChange(f.key)}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-sm transition-colors duration-150 ${
              active
                ? "bg-content text-ink"
                : "bg-surface-2 text-muted hover:bg-edge hover:text-content"
            }`}
          >
            {f.label}
            <span
              className={`min-w-4 rounded-full px-1 text-center text-[11px] ${
                active ? "bg-ink/10 text-ink" : "bg-ink/40 text-faint"
              }`}
            >
              {countFor(f.key)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

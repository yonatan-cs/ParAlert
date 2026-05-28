const FILTERS = [
  { key: "all", label: "הכל" },
  { key: "victim", label: "קורבן" },
  { key: "aggressor", label: "תוקף" },
  { key: "bystander", label: "צופה" },
];

export default function FilterBar({ value, onChange }) {
  return (
    <div className="mb-4 flex gap-2">
      {FILTERS.map((f) => (
        <button
          key={f.key}
          type="button"
          onClick={() => onChange(f.key)}
          className={`rounded-full px-3 py-1 text-sm transition ${
            value === f.key
              ? "bg-slate-200 text-slate-900"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}

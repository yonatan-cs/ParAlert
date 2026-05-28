// 3-angle breakdown — the product's core framing, made visual for the parent/judge.
const ANGLES = [
  { role: "victim", label: "קורבן", color: "text-red-300", ring: "ring-red-500/40" },
  { role: "aggressor", label: "תוקף", color: "text-amber-300", ring: "ring-amber-500/40" },
  { role: "bystander", label: "צופה", color: "text-sky-300", ring: "ring-sky-500/40" },
];

export default function SummaryBar({ alerts }) {
  const counts = { victim: 0, aggressor: 0, bystander: 0 };
  for (const a of alerts) {
    if (counts[a.role_of_child] !== undefined) counts[a.role_of_child] += 1;
  }

  return (
    <div className="mb-6">
      <div className="mb-2 text-xs text-slate-500">הילד שלי, ב-3 זוויות</div>
      <div className="grid grid-cols-3 gap-3">
        {ANGLES.map((a) => (
          <div
            key={a.role}
            className={`rounded-xl bg-slate-800 p-4 text-center ring-1 ${a.ring}`}
          >
            <div className={`text-2xl font-bold ${a.color}`}>{counts[a.role]}</div>
            <div className="text-xs text-slate-400">{a.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

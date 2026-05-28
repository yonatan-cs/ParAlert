// At-a-glance: the 3 bullying angles + the two new dimensions (police-severe, disinfo).
const ANGLES = [
  { role: "victim", label: "קורבן", dot: "bg-victim" },
  { role: "aggressor", label: "תוקף", dot: "bg-aggressor" },
  { role: "bystander", label: "צופה", dot: "bg-bystander" },
];

export default function SummaryBar({ alerts }) {
  const counts = { victim: 0, aggressor: 0, bystander: 0 };
  let police = 0;
  let disinfo = 0;
  for (const a of alerts) {
    if (counts[a.role_of_child] !== undefined) counts[a.role_of_child] += 1;
    if (a.escalation === "police") police += 1;
    if (a.alert_type === "disinformation") disinfo += 1;
  }

  return (
    <section className="mb-5 rounded-2xl border border-edge bg-surface px-2 py-3">
      <div className="grid grid-cols-3 divide-x divide-edge [&>*]:px-2">
        {ANGLES.map((a) => {
          const n = counts[a.role];
          return (
            <div
              key={a.role}
              className={`flex flex-col items-center gap-1 transition-opacity duration-200 ${
                n === 0 ? "opacity-40" : "opacity-100"
              }`}
            >
              <span className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${a.dot}`} />
                <span className="text-2xl font-bold leading-none">{n}</span>
              </span>
              <span className="text-xs text-muted">הילד שלי כ{a.label}</span>
            </div>
          );
        })}
      </div>

      {(police > 0 || disinfo > 0) && (
        <div className="mt-3 flex flex-wrap justify-center gap-2 border-t border-edge pt-3 text-xs">
          {police > 0 && (
            <span className="rounded-full bg-sev-high/15 px-3 py-1 font-medium text-sev-high">
              🚨 {police} דורשות פנייה למשטרה
            </span>
          )}
          {disinfo > 0 && (
            <span className="rounded-full bg-accent/15 px-3 py-1 font-medium text-accent">
              📰 {disinfo} דיסאינפורמציה
            </span>
          )}
        </div>
      )}
    </section>
  );
}

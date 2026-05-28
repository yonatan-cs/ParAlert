const SEV_BORDER = {
  high: "border-red-500",
  medium: "border-amber-500",
  low: "border-green-500",
};

const ROLE_HE = {
  victim: "הילד שלי — קורבן",
  aggressor: "הילד שלי — תוקף",
  bystander: "הילד שלי — צופה",
  none: "—",
};

function Bubble({ bubble, trigger = false }) {
  return (
    <div
      className={`my-1.5 rounded-xl px-3 py-2 text-sm ${
        trigger ? "bg-red-900/70 font-semibold" : "bg-slate-900"
      }`}
    >
      <span className="block text-[11px] text-slate-400">{bubble.sender_name}</span>
      {bubble.text}
    </div>
  );
}

export default function AlertCard({ alert, isNew = false }) {
  const pct = Math.round((alert.toxicity_score ?? 0) * 100);
  const border = SEV_BORDER[alert.severity] || "border-slate-500";

  return (
    <div
      className={`mb-4 rounded-2xl border-r-4 bg-slate-800 p-5 shadow-lg ${border} ${
        isNew ? "animate-enter" : ""
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="font-semibold">{alert.group_name}</span>
        <span className="rounded-full bg-slate-700 px-2.5 py-1 text-xs">
          {ROLE_HE[alert.role_of_child] || alert.role_of_child}
        </span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-slate-700">
        <div
          className="h-full"
          style={{
            width: `${pct}%`,
            background: "linear-gradient(to left, #22c55e, #f59e0b, #ef4444)",
          }}
        />
      </div>
      <div className="mb-3 mt-1.5 text-xs text-slate-400">
        מדד רעילות: {pct}% · {alert.category}
      </div>

      {(alert.context_before || []).map((b, i) => (
        <Bubble key={`b${i}`} bubble={b} />
      ))}
      <Bubble bubble={alert.trigger_message} trigger />
      {(alert.context_after || []).map((b, i) => (
        <Bubble key={`a${i}`} bubble={b} />
      ))}

      <div className="mt-3 rounded-xl bg-cyan-950 p-3 text-sm">
        <strong className="mb-1 block text-cyan-300">המלצה לפעולה</strong>
        {alert.recommendation}
      </div>
    </div>
  );
}

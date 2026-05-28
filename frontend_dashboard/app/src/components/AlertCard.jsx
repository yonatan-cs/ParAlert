import { CATEGORY_HE, ROLE_HE, SEVERITY_HE, relativeTime } from "../lib/format.js";

const SEV = {
  high: { dot: "bg-sev-high", badge: "bg-sev-high/15 text-sev-high", fill: "bg-sev-high" },
  medium: { dot: "bg-sev-medium", badge: "bg-sev-medium/15 text-sev-medium", fill: "bg-sev-medium" },
  low: { dot: "bg-sev-low", badge: "bg-sev-low/15 text-sev-low", fill: "bg-sev-low" },
};

function Bubble({ bubble, trigger = false }) {
  return (
    <div
      className={`my-1 rounded-xl px-3 py-2 text-sm ${
        trigger
          ? "bg-sev-high/12 text-content ring-1 ring-sev-high/30"
          : "bg-ink text-muted"
      }`}
    >
      <span className="mb-0.5 block text-[11px] text-faint">{bubble.sender_name}</span>
      {bubble.text}
    </div>
  );
}

export default function AlertCard({ alert, isNew = false }) {
  const pct = Math.round((alert.toxicity_score ?? 0) * 100);
  const sev = SEV[alert.severity] || SEV.low;

  return (
    <article
      className={`mb-3 rounded-2xl border border-edge bg-surface p-5 shadow-[0_1px_2px_oklch(0_0_0/0.3),0_8px_24px_oklch(0_0_0/0.18)] ${
        isNew ? "animate-enter" : ""
      }`}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-start gap-2.5">
          <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${sev.dot}`} />
          <div>
            <h3 className="font-semibold leading-tight">{alert.group_name}</h3>
            <span className="text-[11px] text-faint">{relativeTime(alert.created_at)}</span>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${sev.badge}`}>
            {SEVERITY_HE[alert.severity] || alert.severity}
          </span>
          <span className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-muted">
            {ROLE_HE[alert.role_of_child] || alert.role_of_child}
          </span>
        </div>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
        <div className={`meter-fill h-full rounded-full ${sev.fill}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="mb-3 mt-1.5 text-xs text-faint">
        מדד רעילות {pct}% · {CATEGORY_HE[alert.category] || alert.category}
      </div>

      {(alert.context_before || []).map((b, i) => (
        <Bubble key={`b${i}`} bubble={b} />
      ))}
      <Bubble bubble={alert.trigger_message} trigger />
      {(alert.context_after || []).map((b, i) => (
        <Bubble key={`a${i}`} bubble={b} />
      ))}

      <div className="mt-3 rounded-xl bg-accent/10 p-3 text-sm ring-1 ring-accent/20">
        <strong className="mb-1 block text-accent">המלצה לפעולה</strong>
        <span className="text-content">{alert.recommendation}</span>
      </div>
    </article>
  );
}

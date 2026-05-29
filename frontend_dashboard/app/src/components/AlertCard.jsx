import { useState } from "react";
import { useI18n } from "../i18n/I18nContext.jsx";
import { relativeTime } from "../lib/format.js";
import { downloadEvidence } from "../lib/evidence.js";

const SEV = {
  high: { dot: "bg-sev-high", badge: "bg-sev-high/15 text-sev-high", fill: "bg-sev-high" },
  medium: { dot: "bg-sev-medium", badge: "bg-sev-medium/15 text-sev-medium", fill: "bg-sev-medium" },
  low: { dot: "bg-sev-low", badge: "bg-sev-low/15 text-sev-low", fill: "bg-sev-low" },
};

const SENSITIVE = new Set(["nudity", "sexual", "sexual_harassment"]);

// Shows the actual media the child received. Sensitive content is blurred (the
// parent can reveal it) — the system only reports, it can't block WhatsApp.
function MediaPreview({ bubble, sensitive }) {
  const { t } = useI18n();
  const [revealed, setRevealed] = useState(false);
  if (!bubble.media_type) return null;
  const isVideo = bubble.media_type === "video";
  const url = bubble.media_url || "https://picsum.photos/seed/safenet/480/300";
  const blurred = sensitive && !revealed;

  return (
    <div className="relative mt-2 overflow-hidden rounded-md bg-black/20">
      <img
        src={url}
        alt=""
        loading="lazy"
        className={`max-h-52 w-full object-cover transition duration-300 ${blurred ? "scale-110 blur-2xl" : ""}`}
      />
      {isVideo && !blurred && (
        <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-4xl text-white/90 drop-shadow">
          ▶
        </span>
      )}
      {isVideo && (
        <span className="absolute bottom-1 start-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-white">
          {t.card.video}
        </span>
      )}
      {blurred && (
        <button
          type="button"
          onClick={() => setRevealed(true)}
          className="absolute inset-0 flex flex-col items-center justify-center gap-1 bg-black/35 text-xs font-medium text-white"
        >
          <span>{t.card.sensitive}</span>
          <span className="underline">{t.card.reveal}</span>
        </button>
      )}
    </div>
  );
}

function Bubble({ bubble, trigger = false, sensitive = false }) {
  return (
    <div
      className={`my-1 rounded-md px-3 py-2 text-sm ${
        trigger ? "bg-sev-high/12 text-content ring-1 ring-sev-high/30" : "bg-surface-2 text-muted"
      }`}
    >
      <span className="mb-0.5 block text-[11px] text-faint">{bubble.sender_name}</span>
      {bubble.text}
      <MediaPreview bubble={bubble} sensitive={sensitive} />
    </div>
  );
}

function EscalationBanner({ escalation }) {
  const { t } = useI18n();
  if (!escalation || escalation === "none") return null;
  const cls =
    "mb-3 flex items-center gap-2 rounded-md bg-sev-high px-3 py-2.5 text-sm font-semibold text-white shadow";
  const body = <span>🚨 {t.escalation[escalation] || ""}</span>;
  return escalation === "police" ? (
    <a href="tel:100" className={cls}>
      {body}
    </a>
  ) : (
    <div className={cls}>{body}</div>
  );
}

// Police-severe alerts only. The conversation we already render IS the evidence —
// this offers it as a downloadable screenshot to attach to a police report.
function EvidenceSection({ alert }) {
  const { t, locale, dir } = useI18n();
  return (
    <button
      type="button"
      onClick={() => downloadEvidence(alert, { t, locale, dir })}
      className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-sev-high/30 bg-sev-high/10 px-3 py-1.5 text-xs font-medium text-sev-high transition hover:bg-sev-high/15"
    >
      ⬇ {t.card.evidenceDownload}
    </button>
  );
}

function CredibilitySection({ c }) {
  const { t } = useI18n();
  const pct = Math.round((c.score ?? 0) * 100);
  return (
    <>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
        {/* fill = disinformation risk (1 - credibility), in red */}
        <div className="meter-fill h-full rounded-full bg-sev-high" style={{ width: `${100 - pct}%` }} />
      </div>
      <div className="mb-2 mt-1.5 text-xs text-faint">
        {t.card.credibility} {pct}% · {c.verdict}
      </div>
      <div className="rounded-md bg-surface-2 p-3 text-sm">
        <span className="mb-0.5 block text-[11px] text-faint">{t.card.claimChecked}</span>
        {c.claim}
        {c.source && <span className="mt-1 block text-[11px] text-faint">{t.card.source}: {c.source}</span>}
      </div>
    </>
  );
}

export default function AlertCard({ alert, isNew = false }) {
  const { t, locale } = useI18n();
  const sev = SEV[alert.severity] || SEV.low;
  const isDisinfo = alert.alert_type === "disinformation";
  const sensitive = SENSITIVE.has(alert.category);
  const toxPct = Math.round((alert.toxicity_score ?? 0) * 100);

  return (
    <article
      className={`card-elev mb-4 break-inside-avoid rounded-lg border bg-surface p-5 ${
        alert.escalation === "police" ? "border-sev-high/50" : "border-edge"
      } ${isNew ? "animate-enter" : ""}`}
    >
      <EscalationBanner escalation={alert.escalation} />

      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-start gap-2.5">
          <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${sev.dot}`} />
          <div>
            <h3 className="font-semibold leading-tight">{alert.group_name}</h3>
            <span className="text-[11px] text-faint">{relativeTime(alert.created_at, locale)}</span>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          {isDisinfo && (
            <span className="rounded-md bg-accent/15 px-2.5 py-1 text-xs text-accent">{t.card.disinfoBadge}</span>
          )}
          <span className={`rounded-md px-2.5 py-1 text-xs font-medium ${sev.badge}`}>
            {t.severity[alert.severity] || alert.severity}
          </span>
          <span className="rounded-md bg-surface-2 px-2.5 py-1 text-xs text-muted">
            {t.role[alert.role_of_child] || alert.role_of_child}
          </span>
        </div>
      </div>

      {isDisinfo && alert.credibility ? (
        <CredibilitySection c={alert.credibility} />
      ) : (
        <>
          <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
            <div className={`meter-fill h-full rounded-full ${sev.fill}`} style={{ width: `${toxPct}%` }} />
          </div>
          <div className="mb-3 mt-1.5 text-xs text-faint">
            {t.card.toxicity} {toxPct}% · {t.category[alert.category] || alert.category}
          </div>
        </>
      )}

      {(alert.context_before || []).map((b, i) => (
        <Bubble key={`b${i}`} bubble={b} sensitive={sensitive} />
      ))}
      <Bubble bubble={alert.trigger_message} trigger sensitive={sensitive} />
      {(alert.context_after || []).map((b, i) => (
        <Bubble key={`a${i}`} bubble={b} sensitive={sensitive} />
      ))}

      {alert.escalation === "police" && <EvidenceSection alert={alert} />}

      <div className="mt-3 rounded-md bg-accent/10 p-3 text-sm ring-1 ring-accent/20">
        <strong className="mb-1 block text-accent">{t.card.recommendation}</strong>
        <span className="text-content">{alert.recommendation}</span>
      </div>
    </article>
  );
}

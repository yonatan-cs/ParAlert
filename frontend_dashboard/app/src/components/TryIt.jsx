import { useState } from "react";
import { useI18n } from "../i18n/I18nContext.jsx";

// Interactive playground: judges submit text / media URL / a file and get a live
// analysis report from the backend (which routes to the real ML models when
// ML_SERVICE_URL is configured, else the keyword fallback). Toxic/disinfo
// submissions also pop as a live alert on the Dashboard.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function pct(x) {
  return Math.round((x || 0) * 100);
}

function Meter({ value, cls }) {
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
      <div className={`meter-fill h-full rounded-full ${cls}`} style={{ width: `${value}%` }} />
    </div>
  );
}

export default function TryIt() {
  const { t } = useI18n();
  const tx = t.tryit;
  const [text, setText] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const canSubmit = Boolean(text.trim() || mediaUrl.trim() || file);

  async function analyze() {
    if (!canSubmit) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      let res;
      if (file) {
        const fd = new FormData();
        fd.append("text", text);
        fd.append("file", file);
        res = await fetch(`${API_BASE}/analyze/upload`, { method: "POST", body: fd });
      } else {
        res = await fetch(`${API_BASE}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, media_url: mediaUrl.trim() || null }),
        });
      }
      if (!res.ok) throw new Error(`status ${res.status}`);
      setResult(await res.json());
    } catch {
      setError(tx.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade space-y-4">
      <div>
        <h2 className="text-lg font-bold">{tx.title}</h2>
        <p className="mt-1 text-sm text-muted">{tx.subtitle}</p>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={tx.placeholder}
        rows={3}
        className="w-full resize-none rounded-xl border border-edge bg-ink px-3 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30"
      />

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-faint">{tx.samplesLabel}</span>
        {tx.samples.map((s) => (
          <button
            key={s.label}
            type="button"
            onClick={() => {
              setText(s.text);
              setFile(null);
              setMediaUrl("");
            }}
            className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-muted transition-colors hover:bg-edge hover:text-content"
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          value={mediaUrl}
          onChange={(e) => setMediaUrl(e.target.value)}
          placeholder={tx.mediaUrlPlaceholder}
          dir="ltr"
          disabled={Boolean(file)}
          className="min-w-0 flex-1 rounded-xl border border-edge bg-ink px-3 py-2 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30 disabled:opacity-40"
        />
        <label className="flex cursor-pointer items-center justify-center rounded-xl border border-edge bg-surface-2 px-3 py-2 text-xs text-muted transition-colors hover:text-content">
          {file ? file.name : tx.uploadLabel}
          <input
            type="file"
            accept="image/*,video/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="hidden"
          />
        </label>
      </div>

      <button
        type="button"
        onClick={analyze}
        disabled={!canSubmit || loading}
        className="w-full rounded-xl bg-accent py-2.5 text-sm font-semibold text-ink transition disabled:opacity-40"
      >
        {loading ? tx.analyzing : tx.analyze}
      </button>

      {error && (
        <div className="rounded-xl bg-sev-high/15 px-3 py-2 text-sm text-sev-high">{error}</div>
      )}

      {result && <Report r={result} tx={tx} t={t} />}
    </div>
  );
}

function Report({ r, tx, t }) {
  const isDisinfo = r.alert_type === "disinformation" && r.credibility;
  const tone = r.is_toxic ? "high" : isDisinfo ? "disinfo" : "clean";
  const TONE = {
    high: { box: "border-sev-high/50 bg-sev-high/10", text: "text-sev-high", fill: "bg-sev-high", label: tx.verdictBullying, icon: "🛡️" },
    disinfo: { box: "border-accent/40 bg-accent/10", text: "text-accent", fill: "bg-accent", label: tx.verdictDisinfo, icon: "📰" },
    clean: { box: "border-sev-low/40 bg-sev-low/10", text: "text-sev-low", fill: "bg-sev-low", label: tx.verdictClean, icon: "✓" },
  }[tone];
  const toxPct = pct(r.toxicity_score);
  const realModel = r.model_used && !r.model_used.includes("keyword") && r.model_used !== "stub";

  return (
    <article className={`animate-enter space-y-3 rounded-2xl border p-4 ${TONE.box}`}>
      <div className="flex items-center justify-between gap-2">
        <span className={`flex items-center gap-2 font-semibold ${TONE.text}`}>
          <span className="text-lg">{TONE.icon}</span>
          {TONE.label}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] ${
            realModel ? "bg-sev-low/15 text-sev-low" : "bg-surface-2 text-faint"
          }`}
          title={r.model_used}
        >
          {realModel ? tx.realModelTag : tx.keywordTag}
        </span>
      </div>

      {!isDisinfo && (
        <div>
          <Meter value={toxPct} cls={TONE.fill} />
          <div className="mt-1.5 text-xs text-faint">
            {tx.toxicity} {toxPct}% · {t.category[r.category] || r.category}
          </div>
        </div>
      )}

      {r.media && (
        <div className="space-y-2 rounded-xl bg-surface-2 p-3">
          <div>
            <div className="mb-1 flex justify-between text-xs text-faint">
              <span>{tx.nsfw}</span>
              <span>{pct(r.media.safety_score)}%</span>
            </div>
            <Meter value={pct(r.media.safety_score)} cls="bg-sev-high" />
          </div>
          <div>
            <div className="mb-1 flex justify-between text-xs text-faint">
              <span>{tx.deepfake}</span>
              <span>{pct(r.media.ai_score)}%</span>
            </div>
            <Meter value={pct(r.media.ai_score)} cls="bg-sev-medium" />
          </div>
        </div>
      )}

      {isDisinfo && (
        <div>
          <Meter value={100 - pct(r.credibility.score)} cls="bg-sev-high" />
          <div className="mt-1.5 text-xs text-faint">
            {t.card.credibility} {pct(r.credibility.score)}% · {r.credibility.verdict}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-2 text-[11px] text-faint">
        <span className="truncate">{tx.modelLabel}: {r.model_used || "—"}</span>
        {r.alert_created && <span className="shrink-0 text-accent">{tx.popped}</span>}
      </div>
    </article>
  );
}

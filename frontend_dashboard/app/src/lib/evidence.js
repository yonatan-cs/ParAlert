// Client-side "evidence package" for severe (police) alerts. Renders the alert's
// conversation thread — context_before + trigger_message + context_after — to a
// PNG the parent can attach to a police report. Demo-grade: it screenshots the
// messages we already hold, no server round-trip.

const W = 760; // logical width (canvas is drawn at 2x for crisp text)
const PAD = 24;
const BUBBLE_PAD = 14;
const LINE_H = 22;
const START_Y = 120; // below the header band
const FOOTER_H = 38;

const FONT = '15px "Assistant", system-ui, -apple-system, sans-serif';
const NAME_FONT = '600 12px "Assistant", system-ui, -apple-system, sans-serif';

// Theme-independent palette — evidence is for printing/sharing, so a light,
// high-contrast sheet reads best regardless of the dashboard theme.
const C = {
  paper: "#ffffff",
  band: "#b91c1c",
  bandText: "#ffffff",
  group: "#0f172a",
  time: "#64748b",
  bubbleBg: "#f1f5f9",
  bubbleText: "#0f172a",
  name: "#64748b",
  triggerBg: "#fee2e2",
  triggerBorder: "#ef4444",
  triggerText: "#7f1d1d",
  media: "#475569",
  footer: "#94a3b8",
};

function messagesOf(alert) {
  return [
    ...(alert.context_before || []).map((b) => ({ ...b, trigger: false })),
    { ...(alert.trigger_message || {}), trigger: true },
    ...(alert.context_after || []).map((b) => ({ ...b, trigger: false })),
  ].filter((m) => m && (m.text || m.media_type));
}

function wrapText(ctx, text, maxWidth) {
  const words = String(text || "").split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines.length ? lines : [""];
}

function mediaLabel(m, t) {
  if (!m.media_type) return null;
  const word = m.media_type === "video" ? (t?.card?.video || "video") : "image";
  return `📎 [${word}]`;
}

// Returns a fully drawn <canvas> (offscreen). Caller turns it into a data URL or blob.
export function buildEvidenceCanvas(alert, { t, locale = "he", dir = "rtl" } = {}) {
  const msgs = messagesOf(alert);
  const innerW = W - PAD * 2;
  const textMax = innerW - BUBBLE_PAD * 2;

  // Pass 1 — measure heights with a throwaway context.
  const measure = document.createElement("canvas").getContext("2d");
  measure.font = FONT;

  let y = START_Y;
  const laid = msgs.map((m) => {
    const lines = wrapText(measure, m.text, textMax);
    const hasMedia = !!m.media_type;
    const h = BUBBLE_PAD + 20 /* name + gap */ + lines.length * LINE_H + (hasMedia ? 22 : 0) + BUBBLE_PAD - 6;
    const block = { m, lines, hasMedia, y, h };
    y += h + 10;
    return block;
  });
  const totalH = y + FOOTER_H;

  // Pass 2 — draw at 2x.
  const scale = 2;
  const canvas = document.createElement("canvas");
  canvas.width = W * scale;
  canvas.height = totalH * scale;
  const ctx = canvas.getContext("2d");
  ctx.scale(scale, scale);
  ctx.textBaseline = "top";
  ctx.direction = dir;

  const rtl = dir === "rtl";
  const align = rtl ? "right" : "left";
  // x-anchor for text inside a bubble (or full-width header), given left/right padding.
  const textX = (leftEdge, width, padX) => (rtl ? leftEdge + width - padX : leftEdge + padX);

  // Background sheet.
  ctx.fillStyle = C.paper;
  ctx.fillRect(0, 0, W, totalH);

  // Header band.
  ctx.fillStyle = C.band;
  ctx.fillRect(0, 0, W, 60);
  ctx.textAlign = align;
  ctx.fillStyle = C.bandText;
  ctx.font = '700 20px "Assistant", system-ui, sans-serif';
  const title = `ParAlert · ${t?.card?.evidenceTitle || "Conversation evidence"}`;
  ctx.fillText(title, textX(0, W, PAD), 18);

  // Group name + timestamp.
  ctx.textAlign = align;
  ctx.fillStyle = C.group;
  ctx.font = '600 16px "Assistant", system-ui, sans-serif';
  ctx.fillText(alert.group_name || "—", textX(0, W, PAD), 76);
  ctx.fillStyle = C.time;
  ctx.font = '12px "Assistant", system-ui, sans-serif';
  let stamp = alert.created_at || "";
  try {
    stamp = new Date(alert.created_at).toLocaleString(locale);
  } catch {
    /* keep raw */
  }
  ctx.fillText(stamp, textX(0, W, PAD), 97);

  // Bubbles.
  for (const b of laid) {
    const trig = b.m.trigger;
    ctx.fillStyle = trig ? C.triggerBg : C.bubbleBg;
    ctx.beginPath();
    ctx.roundRect(PAD, b.y, innerW, b.h, 10);
    ctx.fill();
    if (trig) {
      ctx.strokeStyle = C.triggerBorder;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    const ax = textX(PAD, innerW, BUBBLE_PAD);
    ctx.textAlign = align;
    let ty = b.y + BUBBLE_PAD;

    ctx.fillStyle = C.name;
    ctx.font = NAME_FONT;
    ctx.fillText(b.m.sender_name || "—", ax, ty);
    ty += 20;

    ctx.fillStyle = trig ? C.triggerText : C.bubbleText;
    ctx.font = FONT;
    for (const line of b.lines) {
      ctx.fillText(line, ax, ty);
      ty += LINE_H;
    }

    if (b.hasMedia) {
      ctx.fillStyle = C.media;
      ctx.font = '13px "Assistant", system-ui, sans-serif';
      ctx.fillText(mediaLabel(b.m, t), ax, ty);
    }
  }

  // Footer watermark.
  ctx.textAlign = align;
  ctx.fillStyle = C.footer;
  ctx.font = '11px "Assistant", system-ui, sans-serif';
  ctx.fillText(
    `${t?.card?.evidenceFooter || "Generated by ParAlert — demo evidence"} · ${stamp}`,
    textX(0, W, PAD),
    totalH - FOOTER_H + 12,
  );

  return canvas;
}

export function evidenceDataUrl(alert, opts) {
  return buildEvidenceCanvas(alert, opts).toDataURL("image/png");
}

export function downloadEvidence(alert, opts) {
  const canvas = buildEvidenceCanvas(alert, opts);
  const safe = (alert.group_name || "chat").replace(/[^\p{L}\p{N}_-]+/gu, "_").slice(0, 40);
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ParAlert-evidence-${safe}.png`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, "image/png");
}

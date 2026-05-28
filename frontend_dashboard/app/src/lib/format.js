// Locale-aware relative time. Intl.RelativeTimeFormat gives correct grammar in
// both Hebrew and English; "now" is special-cased for a cleaner reading.
// (Hebrew label maps moved to src/i18n/translations.js.)

export function relativeTime(iso, locale = "he-IL") {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  // Demo timestamps can be later "today"; clamp the future to "now" so we never
  // render "in 17 minutes". Always shown as past ("… ago" / "לפני …").
  const sec = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (sec < 60) return locale.startsWith("he") ? "עכשיו" : "now";
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  if (sec < 3600) return rtf.format(-Math.round(sec / 60), "minute");
  if (sec < 86400) return rtf.format(-Math.round(sec / 3600), "hour");
  return rtf.format(-Math.round(sec / 86400), "day");
}

// Hebrew label maps + helpers, shared across components. Keys match contract C.

export const CATEGORY_HE = {
  harassment: "הטרדה",
  threat: "איום",
  exclusion: "נידוי חברתי",
  hate_speech: "שיח שנאה",
  sexual: "תוכן מיני",
  none: "—",
};

export const ROLE_HE = {
  victim: "הילד שלי — קורבן",
  aggressor: "הילד שלי — תוקף",
  bystander: "הילד שלי — צופה",
  none: "—",
};

export const SEVERITY_HE = {
  high: "חמור",
  medium: "בינוני",
  low: "קל",
};

export function relativeTime(iso) {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const sec = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (sec < 60) return "עכשיו";
  const min = Math.round(sec / 60);
  if (min < 60) return `לפני ${min} ${min === 1 ? "דקה" : "דקות"}`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `לפני ${hr} ${hr === 1 ? "שעה" : "שעות"}`;
  const day = Math.round(hr / 24);
  return `לפני ${day} ${day === 1 ? "יום" : "ימים"}`;
}

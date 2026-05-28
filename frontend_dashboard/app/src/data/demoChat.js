// Scripted conversation for the demo opener (the child's group chat).
// MUST stay in sync with the two "כיתה ו'2" alerts in contracts/mock_alerts.json
// (alert_001 harassment + alert_003 threat) so the chat the judge watches matches
// exactly what appears on the dashboard. `toxic` drives the alert flash.
export const DEMO_GROUP = "כיתה ו'2 - בלי המורה";

export const DEMO_CHAT = [
  { sender: "יונתן", fromChild: true, text: "מתי קובעים למשחק היום?", delayMs: 700 },
  { sender: "רון", fromChild: false, text: "אחרי הצהריים בפארק", delayMs: 1100 },
  { sender: "דני", fromChild: false, text: "יונתן אל תבוא, אף אחד לא רוצה אותך", toxic: true, delayMs: 1600 },
  { sender: "דני", fromChild: false, text: "איזה אפס אתה בכלל", toxic: true, delayMs: 1300 },
  { sender: "נועה", fromChild: false, text: "תפסיקו כבר", delayMs: 1200 },
  { sender: "איתי", fromChild: false, text: "אם תספר למורה אני מחכה לך אחרי בית ספר", toxic: true, delayMs: 1600 },
];

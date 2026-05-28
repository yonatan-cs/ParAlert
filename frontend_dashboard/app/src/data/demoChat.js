// Scripted conversation for the demo opener (the child's group chat).
// Mirrors simulator_and_logic/conversations/escalation_demo.json.
// `fromChild` = the monitored kid; `toxic` only drives the demo's alert flash.
export const DEMO_GROUP = "כיתה ו'2 - בלי המורה";

export const DEMO_CHAT = [
  { sender: "יונתן", fromChild: true, text: "מתי קובעים למשחק היום?", delayMs: 700 },
  { sender: "רון", fromChild: false, text: "אחרי הצהריים בפארק", delayMs: 1100 },
  { sender: "דני", fromChild: false, text: "יונתן אל תבוא, אף אחד לא רוצה אותך", toxic: true, delayMs: 1600 },
  { sender: "דני", fromChild: false, text: "איזה אפס אתה בכלל", toxic: true, delayMs: 1300 },
  { sender: "נועה", fromChild: false, text: "תפסיקו כבר נו", delayMs: 1200 },
  { sender: "דני", fromChild: false, text: "כולם נגדך פה תתרגל", toxic: true, delayMs: 1500 },
];

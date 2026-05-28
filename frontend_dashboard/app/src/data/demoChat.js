// Multi-group demo scenarios for the chat opener ("הפעל").
// Each group's flagged messages match a dashboard alert in
// contracts/mock_alerts.json (kept in sync) so what the judge watches escalate
// equals what pops on the dashboard.
// flags: toxic = bullying · severe = police escalation · disinfo = credibility.
export const DEMO_SCENARIOS = [
  {
    group: "כיתה ו'2 - בלי המורה",
    members: "5 משתתפים",
    messages: [
      { sender: "יונתן", fromChild: true, text: "מתי קובעים למשחק היום?", delayMs: 700 },
      { sender: "רון", text: "אחרי הצהריים בפארק", delayMs: 1100 },
      { sender: "דני", text: "יונתן אל תבוא, אף אחד לא רוצה אותך", toxic: true, delayMs: 1500 },
      { sender: "דני", text: "איזה אפס אתה בכלל", toxic: true, delayMs: 1200 },
      { sender: "נועה", text: "תפסיקו כבר", delayMs: 1100 },
      { sender: "איתי", text: "אם תספר למורה אני מחכה לך אחרי בית ספר", toxic: true, severe: true, delayMs: 1500 },
    ],
  },
  {
    group: "שכבה ז' - צ'אט כללי",
    members: "קבוצה גדולה",
    messages: [
      { sender: "מספר לא מוכר", text: "היי, ראיתי אותך, את ממש יפה", delayMs: 900 },
      { sender: "מספר לא מוכר", text: "שלחי לי תמונה שלך בלי בגדים או שאני מפיץ את מה שיש לי", media: "image", toxic: true, severe: true, delayMs: 1700 },
    ],
  },
  {
    group: "חדשות הכיתה 📰",
    members: "12 משתתפים",
    messages: [
      { sender: "ליאור", text: "תראו את הסרטון הזה!! חיסון הקורונה גורם ל... חייבים לשתף", media: "video", disinfo: true, delayMs: 1500 },
      { sender: "יונתן", fromChild: true, text: "וואו לא ידעתי, אשתף", delayMs: 1300 },
    ],
  },
  {
    group: "קבוצה אנונימית 🔞",
    members: "אנונימי",
    messages: [
      { sender: "אנונימי", text: "הופצה תמונה פוגענית של הילדה שלך", media: "image", toxic: true, severe: true, delayMs: 1500 },
    ],
  },
];

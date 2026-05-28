// Multi-group demo scenarios for the chat opener ("Play"), per language.
// Each group's flagged messages match a dashboard alert in contracts/mock_alerts.json
// (kept in sync) so what the judge watches escalate equals what pops on the dashboard.
// flags: toxic = bullying · severe = police escalation · disinfo = credibility.
export const DEMO_SCENARIOS = {
  he: [
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
        { sender: "מספר לא מוכר", text: "שלחי לי תמונה שלך בלי בגדים או שאני מפיץ את מה שיש לי", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-a/480/300", toxic: true, severe: true, delayMs: 1700 },
      ],
    },
    {
      group: "חדשות הכיתה 📰",
      members: "12 משתתפים",
      messages: [
        { sender: "ליאור", text: "תראו את הסרטון הזה!! חיסון הקורונה גורם ל... חייבים לשתף", media: "video", mediaUrl: "https://picsum.photos/seed/safenet-vid/480/300", disinfo: true, delayMs: 1500 },
        { sender: "יונתן", fromChild: true, text: "וואו לא ידעתי, אשתף", delayMs: 1300 },
      ],
    },
    {
      group: "כיתה ח'1 🎒",
      members: "28 משתתפים",
      messages: [
        { sender: "מספר לא מוכר", text: "תראו את זה 👀", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-b/480/300", toxic: true, severe: true, delayMs: 1500 },
      ],
    },
  ],

  en: [
    {
      group: "Class 6-2 — without the teacher",
      members: "5 members",
      messages: [
        { sender: "Jonathan", fromChild: true, text: "When are we setting up today's game?", delayMs: 700 },
        { sender: "Ron", text: "This afternoon at the park", delayMs: 1100 },
        { sender: "Danny", text: "Jonathan don't come, nobody wants you", toxic: true, delayMs: 1500 },
        { sender: "Danny", text: "You're such a loser", toxic: true, delayMs: 1200 },
        { sender: "Noa", text: "Stop it already", delayMs: 1100 },
        { sender: "Itay", text: "If you tell the teacher I'll be waiting for you after school", toxic: true, severe: true, delayMs: 1500 },
      ],
    },
    {
      group: "Grade 7 — general chat",
      members: "Large group",
      messages: [
        { sender: "Unknown number", text: "Hey, I saw you, you're really pretty", delayMs: 900 },
        { sender: "Unknown number", text: "Send me a photo of you with no clothes, or I'll share what I have", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-a/480/300", toxic: true, severe: true, delayMs: 1700 },
      ],
    },
    {
      group: "Class News 📰",
      members: "12 members",
      messages: [
        { sender: "Lior", text: "Watch this video!! The COVID vaccine causes... we have to share this", media: "video", mediaUrl: "https://picsum.photos/seed/safenet-vid/480/300", disinfo: true, delayMs: 1500 },
        { sender: "Jonathan", fromChild: true, text: "Wow I didn't know, I'll share it", delayMs: 1300 },
      ],
    },
    {
      group: "Class 8-1 🎒",
      members: "28 members",
      messages: [
        { sender: "Unknown number", text: "Look at this 👀", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-b/480/300", toxic: true, severe: true, delayMs: 1500 },
      ],
    },
  ],
};

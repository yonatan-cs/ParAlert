// Multi-group demo scenarios for the chat opener ("Play"), per language.
// Each group mixes normal casual chatter with the flagged messages that match a
// dashboard alert in contracts/mock_alerts.json, so it reads like a real chat.
// flags: toxic = bullying · severe = police escalation · disinfo = credibility.
export const DEMO_SCENARIOS = {
  he: [
    {
      group: "כיתה ו'2 - בלי המורה",
      members: "5 משתתפים",
      messages: [
        { sender: "נועה", text: "מישהו הבין את שיעורי הבית במתמטיקה?", delayMs: 700 },
        { sender: "רון", text: "כן אני אשלח צילום אחר כך 📚", delayMs: 1100 },
        { sender: "יונתן", fromChild: true, text: "מתי קובעים למשחק היום?", delayMs: 1100 },
        { sender: "רון", text: "אחרי הצהריים בפארק", delayMs: 1000 },
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
        { sender: "מאיה", text: "מתי ההגשה של הפרויקט בהיסטוריה?", delayMs: 800 },
        { sender: "תומר", text: "ביום חמישי נראה לי", delayMs: 1000 },
        { sender: "מאיה", text: "תודה! 🙏", delayMs: 900 },
        { sender: "מספר לא מוכר", text: "היי, ראיתי אותך, את ממש יפה", delayMs: 1200 },
        { sender: "מספר לא מוכר", text: "שלחי לי תמונה שלך בלי בגדים או שאני מפיץ את מה שיש לי", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-a/480/300", toxic: true, severe: true, delayMs: 1700 },
      ],
    },
    {
      group: "חדשות הכיתה 📰",
      members: "12 משתתפים",
      messages: [
        { sender: "מאיה", text: "ראיתם את הסרטון מהטיול? 😂", delayMs: 800 },
        { sender: "רון", text: "חחח כן אגדי", delayMs: 900 },
        { sender: "ליאור", text: "תראו את הסרטון הזה!! חיסון הקורונה גורם ל... חייבים לשתף", media: "video", mediaUrl: "https://picsum.photos/seed/safenet-vid/480/300", disinfo: true, delayMs: 1500 },
        { sender: "יונתן", fromChild: true, text: "וואו לא ידעתי, אשתף", delayMs: 1300 },
        { sender: "רון", text: "רגע זה נשמע מוזר...", delayMs: 1100 },
      ],
    },
    {
      group: "כיתה ח'1 🎒",
      members: "28 משתתפים",
      messages: [
        { sender: "שירה", text: "מישהו יודע מתי הטיול השנתי?", delayMs: 800 },
        { sender: "עידן", text: "בשבוע הבא ברביעי", delayMs: 1000 },
        { sender: "יונתן", fromChild: true, text: "אש 🔥", delayMs: 900 },
        { sender: "מספר לא מוכר", text: "תראו את זה 👀", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-b/480/300", toxic: true, severe: true, delayMs: 1500 },
      ],
    },
  ],

  en: [
    {
      group: "Class 6-2 — without the teacher",
      members: "5 members",
      messages: [
        { sender: "Noa", text: "Did anyone get the math homework?", delayMs: 700 },
        { sender: "Ron", text: "Yeah I'll send a photo later 📚", delayMs: 1100 },
        { sender: "Jonathan", fromChild: true, text: "When are we setting up today's game?", delayMs: 1100 },
        { sender: "Ron", text: "This afternoon at the park", delayMs: 1000 },
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
        { sender: "Maya", text: "When's the history project due?", delayMs: 800 },
        { sender: "Tomer", text: "Thursday I think", delayMs: 1000 },
        { sender: "Maya", text: "Thanks! 🙏", delayMs: 900 },
        { sender: "Unknown number", text: "Hey, I saw you, you're really pretty", delayMs: 1200 },
        { sender: "Unknown number", text: "Send me a photo of you with no clothes, or I'll share what I have", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-a/480/300", toxic: true, severe: true, delayMs: 1700 },
      ],
    },
    {
      group: "Class News 📰",
      members: "12 members",
      messages: [
        { sender: "Maya", text: "Did you see the video from the trip? 😂", delayMs: 800 },
        { sender: "Ron", text: "lol yeah legendary", delayMs: 900 },
        { sender: "Lior", text: "Watch this video!! The COVID vaccine causes... we have to share this", media: "video", mediaUrl: "https://picsum.photos/seed/safenet-vid/480/300", disinfo: true, delayMs: 1500 },
        { sender: "Jonathan", fromChild: true, text: "Wow I didn't know, I'll share it", delayMs: 1300 },
        { sender: "Ron", text: "wait this sounds weird...", delayMs: 1100 },
      ],
    },
    {
      group: "Class 8-1 🎒",
      members: "28 members",
      messages: [
        { sender: "Shira", text: "Anyone know when the school trip is?", delayMs: 800 },
        { sender: "Idan", text: "Next week on Wednesday", delayMs: 1000 },
        { sender: "Jonathan", fromChild: true, text: "🔥", delayMs: 900 },
        { sender: "Unknown number", text: "Look at this 👀", media: "image", mediaUrl: "https://picsum.photos/seed/safenet-b/480/300", toxic: true, severe: true, delayMs: 1500 },
      ],
    },
  ],
};

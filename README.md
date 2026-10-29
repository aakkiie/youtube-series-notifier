# 📺 YouTube Next Episode Finder & Telegram Notifier

Ek lightweight, 100% serverless aur open-source tool jo YouTube channels ko track karta hai aur naye anime/series episodes aate hi seedha Telegram par thumbnail poster aur Hinglish summary ke saath notification bhejta hai.

🎉 **Naya Update:** Ab poora system directly Telegram se control hota hai! Kisi code ya JSON file ko manually edit karne ki zaroorat nahi hai.

---

## ✨ Features

- **100% Telegram Controlled:** Nayi series add karni ho ya hatani ho, sab Telegram commands (`/track`, `/stop`, `/list`) se hota hai.
- **100% Mobile Managed:** Phone ke browser se setup ho jata hai, kisi computer ya terminal ki zaroorat nahi.
- **Zero YouTube Data API Quota:** Public RSS feeds use karta hai, isliye koi Google Cloud quota khatam hone ka dar nahi.
- **Smart Episode Matching & AI Fallback:** Regex aur Google Gemini AI ka use karke sirf "next/new" episodes identify karta hai.
- **Secure Control:** Sirf aapka authorized Telegram account hi bot ko commands de sakta hai.

---

## 🚀 Mobile Setup Guide (Phone se Setup kaise karein)

### 1. Repository Fork karein
Upar right corner mein **Fork** button par tap karein aur apne account mein repository create kar lein.

### 2. GitHub Secrets Add karein
Apne repo mein **Settings** > **Secrets and variables** > **Actions** par jayein aur yeh 3 secrets add karein (**New repository secret**):

| Secret Name | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather se mila Telegram bot token |
| `TELEGRAM_CHAT_ID` | Aapka Telegram user ID (jisse sirf aap command de sakein) |
| `GEMINI_API_KEY` | Google AI Studio se mili free Gemini API key |

### 3. Workflow Permissions Enable karein
GitHub Actions ko bot ka data save karne ki permission dene ke liye:
1. Repo **Settings** > Left menu mein **Actions** > **General** par jayein.
2. Niche scroll karke **Workflow permissions** section mein **Read and write permissions** select karein.
3. **Save** par tap karein.

### 4. Engine Start Karein (Pehli Baar)
1. Repo ke **Actions** tab par jayein.
2. **YouTube Channel Tracker** par tap karein.
3. **Run workflow** button press karein. 
*(Pehli run par system initialize ho jayega)*

### 5. Telegram Par Bot Ko Command Dein!
Apne Telegram bot ke chat mein jayein aur type karein:
`/start`

Nayi anime ya series track karne ke liye bas uski YouTube video ka link bhej dein:
`/track https://www.youtube.com/watch?v=...`

⚠️ **Note:** GitHub Actions free tier par yeh bot background mein har 30 minute mein check karta hai, isliye commands ka reply aane mein ~30 minutes tak lag sakte hain. Turant reply chahiye toh Actions tab se workflow manual run kar lein.

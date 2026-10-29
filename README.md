# 📺 YouTube Next Episode Finder & Telegram Notifier

Ek lightweight, 100% serverless aur open-source tool jo YouTube channels ko track karta hai aur naye anime/series episodes aate hi seedha Telegram par thumbnail poster aur Hinglish summary ke saath notification bhejta hai.

Is project ko run karne ke liye kisi computer ya terminal ki zaroorat nahi hai — sab kuch mobile browser aur GitHub Actions ke zariye chalta hai.

---

## ✨ Features

- **100% Mobile Managed:** Phone ke browser se poora setup aur config manage hota hai.
- **Zero YouTube Data API Quota:** Public RSS feeds ka use karta hai, isliye koi Google Cloud console quota khatam hone ka jhanjhat nahi.
- **Smart Episode Matching:** Keyword filtering aur regex detection se sirf naye/agla parts identify karta hai.
- **AI Fallback (Gemini):** Jab creator non-standard title daalta hai, toh Gemini AI context dekh kar confirm karta hai.
- **Rich Telegram Alerts:** Direct video thumbnail poster ke saath caption aur link bhejta hai.
- **Automated State Tracking:** `state.json` ke zariye dekhe huye videos record rehte hain taaki repeat notifications na aayein.

---

## 🚀 Mobile Setup Guide (Phone se Setup kaise karein)

### 1. Repository Fork karein
1. Upar right corner mein **Fork** button par tap karein aur apne account mein repository create kar lein.

### 2. GitHub Secrets Add karein
Apne repo mein **Settings** > **Secrets and variables** > **Actions** par jayein aur yeh 3 secrets add karein (**New repository secret**):

| Secret Name | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather se mila Telegram bot token |
| `TELEGRAM_CHAT_ID` | Aapka Telegram user ID ya channel ID |
| `GEMINI_API_KEY` | Google AI Studio se mili free Gemini API key |

### 3. Workflow Permissions Enable karein
GitHub Actions ko state commit karne ki permission dene ke liye:
1. Repo **Settings** > Left menu mein **Actions** > **General** par jayein.
2. Niche scroll karke **Workflow permissions** section mein **Read and write permissions** select karein.
3. **Save** par tap karein.

### 4. Apni Series Configure karein (`config.json`)
`config.json` file open karke pencil icon dabayein aur apni pasandida series add karein:

```json
{
  "settings": {
    "ai_fallback_on_error": "alert"
  },
  "series": [
    {
      "name": "Target Series Name",
      "channel": "@ChannelHandle",
      "include_keywords": ["Episode", "Part", "Ep"],
      "exclude_keywords": ["Shorts", "Trailer", "Teaser"],
      "last_watched_episode": 0
    }
  ]
}

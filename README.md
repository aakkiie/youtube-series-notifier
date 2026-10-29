# 📺 YouTube Next Episode Finder & Telegram Notifier

A lightweight, 100% serverless, and open-source tool that tracks YouTube channels and sends a Telegram alert with a thumbnail and AI-generated summary whenever a **new episode** is uploaded.

Ek 100% serverless tool jo YouTube par naye episodes aate hi seedha Telegram par thumbnail aur summary ke saath alert bhejta hai.

🎉 **100% Telegram Controlled:** No need to edit code manually. Add, remove, and manage tracked series directly by chatting with your bot! / Code edit karne ki zaroorat nahi, sab kuch Telegram commands se control hota hai.

---

## 🚀 Mobile Setup Guide (English / Hinglish)

You don't need a PC or terminal to set this up. You can do everything from your mobile browser! / Aap isey poori tarah apne phone browser se setup kar sakte hain.

### Step 1: Fork This Repository
Tap the **Fork** button at the top right of this page to copy it to your account. / Upar right corner mein **Fork** button dabayein.

### Step 2: Get Your Secret Keys (Yeh 3 keys zaroori hain)
You need three keys to make this work. / Bot ko chalane ke liye 3 chijein chahiye:

1. **`TELEGRAM_BOT_TOKEN`**: 
   * Go to Telegram and search for `@BotFather`.
   * Send `/newbot`, give it a name, and copy the HTTP API Token it gives you.
2. **`TELEGRAM_CHAT_ID`**: 
   * Search for `@userinfobot` on Telegram and send `/start`.
   * Copy the ID number it replies with. (Only this ID will be able to control the bot).
3. **`GEMINI_API_KEY`**: 
   * Go to [Google AI Studio](https://aistudio.google.com/), sign in, and create a free API key.

### Step 3: Add Secrets to GitHub
1. In your forked repo, go to **Settings** > **Secrets and variables** > **Actions**.
2. Tap **New repository secret** and add the 3 keys above one by one. Exact names matter! / Upar di gayi teeno keys ko yahan save karein.

### Step 4: Enable Permissions
1. Go to repo **Settings** > **Actions** > **General**.
2. Scroll down to **Workflow permissions**, select **Read and write permissions**, and hit **Save**. / Yeh step zaroori hai taaki bot apna data save kar sake.

### Step 5: Start the Engine!
1. Go to the **Actions** tab in your repo.
2. Tap on **YouTube Channel Tracker**.
3. Tap **Run workflow**. (This initializes the bot). / Run dabate hi bot start ho jayega.

### Step 6: Chat with your Bot
Open your newly created bot on Telegram and send:
`/start`

To track a new series, just send the YouTube link:
`/track https://www.youtube.com/watch?v=...`

⚠️ **Note:** The bot runs in the background every 30 minutes (GitHub Free limits). Expect up to a 30-minute delay for replies and alerts. For instant testing, trigger the workflow manually from the Actions tab. / Bot har 30 minute mein check karta hai, isliye reply aane mein 30 min lag sakte hain. Turant reply ke liye Actions tab se manual run karein.

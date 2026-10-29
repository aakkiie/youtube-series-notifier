import os
import sys
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai

# GitHub Secrets se credentials fetch honge
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Aapke YouTube channel ki ID
CHANNEL_ID = "UCeBCrzpdqH0qImV2Ir83_lA"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
LAST_VIDEO_FILE = "last_video.txt"

# Gemini AI Setup
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID environment variable set nahi hai!")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram alert successfully send ho gaya!")
        else:
            print(f"Message send nahi hua: {response.text}")
    except Exception as e:
        print(f"Telegram API call fail ho gayi: {e}")

def get_ai_message(title, link):
    if not GEMINI_API_KEY:
        print("Gemini API key nahi mili, normal message bhej rahe hain.")
        return f"🎬 <b>Nayi Video Update!</b>\n\n📌 <b>{title}</b>\n\n🔗 {link}"
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (f"Batao ki ek nayi YouTube video aayi hai jiska title hai '{title}'. "
                  f"Ek chota, super exciting Telegram message likho Hinglish mein apni taraf se. "
                  f"Mast emojis ka use karo. Markdown stars (**) use mat karna, sirf HTML <b> tags use karna kisi word ko bold karne ke liye. "
                  f"Message ke end mein likho: 'Dekho abhi: {link}'")
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini AI error: {e}. Fallback message use kar rahe hain.")
        return f"🎬 <b>Nayi Video Update!</b>\n\n📌 <b>{title}</b>\n\n🔗 {link}"

def check_latest_video():
    try:
        response = requests.get(RSS_URL, timeout=10)
        if response.status_code != 200:
            print(f"Feed fetch nahi hui, Status code: {response.status_code}")
            return

        root = ET.fromstring(response.content)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015"
        }

        entry = root.find("atom:entry", ns)
        if entry is None:
            print("Feed ke andar koi video nahi mili.")
            return

        video_id = entry.find("yt:videoId", ns).text
        title = entry.find("atom:title", ns).text
        link = entry.find("atom:link", ns).attrib.get("href")

        # Check karein last video ID jo save thi
        last_id = ""
        if os.path.exists(LAST_VIDEO_FILE):
            with open(LAST_VIDEO_FILE, "r") as f:
                last_id = f.read().strip()

        # Nayi video milne par alert bhejein
        if video_id != last_id:
            print(f"Nayi video mili: {title} ({video_id})")
            
            # Yahan hum Gemini AI se message banwa rahe hain
            message = get_ai_message(title, link)
            send_telegram_message(message)

            # Updated video ID file mein save karein
            with open(LAST_VIDEO_FILE, "w") as f:
                f.write(video_id)
        else:
            print("Koi nayi video nahi aayi hai. Sab already updated hai!")

    except Exception as e:
        print(f"Script run karte waqt error aaya: {e}")

if __name__ == "__main__":
    check_latest_video()

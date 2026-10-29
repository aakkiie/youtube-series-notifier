import json
import os
import sys
import xml.etree.ElementTree as ET
import requests
from google import genai

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Telegram credentials missing!")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram alert sent successfully!")
            return True
        else:
            print(f"Send failed: {res.text}")
            return False
    except Exception as e:
        print(f"Telegram API call error: {e}")
        return False

def get_ai_message(title, link):
    fallback_msg = f"<b>Nayi Video Update!</b>\n\n<b>{title}</b>\n\nDekho abhi: {link}"
    if not GEMINI_API_KEY:
        return fallback_msg
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Batao ki ek nayi YouTube video aayi hai jiska title hai '{title}'. "
            f"Ek chota, super exciting Telegram message likho Hinglish mein apni taraf se. "
            f"Mast emojis ka use karo. Markdown stars (**) use mat karna, sirf HTML <b> tags use karna. "
            f"Message ke end mein likho: 'Dekho abhi: {link}'"
        )
        interaction = client.interactions.create(model="gemini-3.8-flash", input=prompt)
        return interaction.output_text.strip()
    except Exception as e:
        print(f"Gemini AI error: {e}. Using fallback.")
        return fallback_msg

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_channel_feed(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch RSS for channel {channel_id}: Status {res.status_code}")
            return []
        root = ET.fromstring(res.content)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015"
        }
        entries = root.findall("atom:entry", ns)
        videos = []
        for entry in entries:
            video_id_el = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            if video_id_el is not None and title_el is not None and link_el is not None:
                videos.append({
                    "id": video_id_el.text.strip(),
                    "title": title_el.text.strip() if title_el.text else "Untitled",
                    "link": link_el.attrib.get("href", "")
                })
        return videos
    except Exception as e:
        print(f"Error fetching/parsing feed for {channel_id}: {e}")
        return []

def main():
    config = load_json(CONFIG_FILE, {"series": []})
    series_list = config.get("series", [])
    if not series_list:
        print("config.json mein koi series nahi mili!")
        return

    state = load_json(STATE_FILE, {})

    unique_channels = {}
    for s in series_list:
        cid = s.get("channel_id", "").strip()
        if cid:
            unique_channels.setdefault(cid, []).append(s)

    for channel_id in unique_channels.keys():
        print(f"\nChecking channel: {channel_id}")
        videos = fetch_channel_feed(channel_id)
        if not videos:
            print(f"No videos found or feed failed for {channel_id}")
            continue

        # Pehli baar run ho raha hai toh current videos save karo bina alert bheje
        if channel_id not in state:
            print(f"First run for channel {channel_id}. Seeding {len(videos)} videos without alert.")
            state[channel_id] = [v["id"] for v in videos]
            save_json(STATE_FILE, state)
            continue

        seen_ids = set(state.get(channel_id, []))
        
        # YouTube feed newest-first deta hai, reversed() se hum oldest-first process karenge
        new_videos = [v for v in reversed(videos) if v["id"] not in seen_ids]

        if not new_videos:
            print(f"Channel {channel_id} up to date. No new videos.")
            continue

        print(f"Found {len(new_videos)} new video(s) for {channel_id}.")
        for vid in new_videos:
            print(f"Processing: {vid['title']} ({vid['id']})")
            msg = get_ai_message(vid["title"], vid["link"])
            send_telegram_message(msg)
            
            # State update karke turant save karte hain taaki crash hone par bhi repeat na ho
            state[channel_id].append(vid["id"])
            save_json(STATE_FILE, state)

if __name__ == "__main__":
    main()

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import requests
from google import genai

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

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

def resolve_to_channel_id(identifier):
    identifier = identifier.strip()
    # Agar pehle se hi UC... channel ID hai
    if identifier.startswith("UC") and len(identifier) == 24:
        return identifier

    # Handle banayein
    handle = identifier if identifier.startswith("@") else f"@{identifier}"
    url = f"https://www.youtube.com/{handle}"
    print(f"Resolving channel ID for handle: {handle}...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"Failed to load channel page {url}: Status {res.status_code}")
            return None

        # Look for channel ID in page meta tags & scripts
        patterns = [
            r'href="https://www.youtube.com/channel/(UC[\w-]{22})"',
            r'"externalId":"(UC[\w-]{22})"',
            r'"browseId":"(UC[\w-]{22})"',
            r'itemprop="identifier" content="(UC[\w-]{22})"'
        ]
        for pattern in patterns:
            match = re.search(pattern, res.text)
            if match:
                channel_id = match.group(1)
                print(f"Found Channel ID: {channel_id}")
                return channel_id

        print(f"Could not extract Channel ID for {handle}")
        return None
    except Exception as e:
        print(f"Error resolving handle {handle}: {e}")
        return None

def fetch_channel_feed(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch RSS for {channel_id}: Status {res.status_code}")
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
    # Make sure state file exists right away
    if not os.path.exists(STATE_FILE):
        save_json(STATE_FILE, {})

    config = load_json(CONFIG_FILE, {"series": []})
    series_list = config.get("series", [])
    if not series_list:
        print("config.json mein koi series nahi mili!")
        return

    state = load_json(STATE_FILE, {})

    # Collect unique channel identifiers (can be @handle or UC... id)
    unique_identifiers = {}
    for s in series_list:
        ident = s.get("channel") or s.get("channel_id") or ""
        ident = ident.strip()
        if ident:
            unique_identifiers.setdefault(ident, []).append(s)

    for ident in unique_identifiers.keys():
        channel_id = resolve_to_channel_id(ident)
        if not channel_id:
            print(f"Skipping {ident} because Channel ID could not be determined.")
            continue

        print(f"\nChecking RSS feed for: {channel_id} ({ident})")
        videos = fetch_channel_feed(channel_id)
        if not videos:
            print(f"No videos found or feed empty for {channel_id}")
            continue

        # First run seed check
        if channel_id not in state:
            print(f"First run for {channel_id}. Seeding {len(videos)} videos without alert.")
            state[channel_id] = [v["id"] for v in videos]
            save_json(STATE_FILE, state)
            continue

        seen_ids = set(state.get(channel_id, []))
        new_videos = [v for v in reversed(videos) if v["id"] not in seen_ids]

        if not new_videos:
            print(f"Channel {channel_id} up to date. No new videos.")
            continue

        print(f"Found {len(new_videos)} new video(s) for {channel_id}.")
        for vid in new_videos:
            print(f"Processing: {vid['title']} ({vid['id']})")
            msg = get_ai_message(vid["title"], vid["link"])
            send_telegram_message(msg)
            
            state[channel_id].append(vid["id"])
            save_json(STATE_FILE, state)

if __name__ == "__main__":
    main()

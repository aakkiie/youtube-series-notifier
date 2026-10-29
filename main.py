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

def get_ai_message(series_name, ep_num, title, link):
    fallback_msg = (
        f"🔥 <b>Naya Episode Alert!</b>\n\n"
        f"📺 <b>{series_name}</b> (Episode {ep_num})\n"
        f"🎬 <b>{title}</b>\n\n"
        f"Dekho abhi: {link}"
    )
    if not GEMINI_API_KEY:
        return fallback_msg
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Batao ki series '{series_name}' ka naya episode/part {ep_num} aa gaya hai! "
            f"Video ka title hai: '{title}'. "
            f"Ek chota, super exciting Telegram alert message likho Hinglish mein. "
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
    if identifier.startswith("UC") and len(identifier) == 24:
        return identifier

    handle = identifier if identifier.startswith("@") else f"@{identifier}"
    url = f"https://www.youtube.com/{handle}"
    print(f"Resolving channel ID for handle: {handle}...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"Failed to load channel page {url}: Status {res.status_code}")
            return None

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
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/"
        }
        entries = root.findall("atom:entry", ns)
        videos = []
        for entry in entries:
            video_id_el = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            
            # Extract description from media:group
            desc = ""
            media_group = entry.find("media:group", ns)
            if media_group is not None:
                desc_el = media_group.find("media:description", ns)
                if desc_el is not None and desc_el.text:
                    desc = desc_el.text.strip()

            if video_id_el is not None and title_el is not None and link_el is not None:
                videos.append({
                    "id": video_id_el.text.strip(),
                    "title": title_el.text.strip() if title_el.text else "Untitled",
                    "link": link_el.attrib.get("href", ""),
                    "description": desc
                })
        return videos
    except Exception as e:
        print(f"Error fetching/parsing feed for {channel_id}: {e}")
        return []

def extract_episode_number(text):
    if not text:
        return None
    
    # 1. Season/Episode format: S2E3 or S02E05
    se_match = re.search(r'(?i)\bs\d+\s*e(\d+)\b', text)
    if se_match:
        return int(se_match.group(1))

    # 2. Episode / Part / Chapter formats: "Part 5", "Ep 5", "Episode 05", "Chapter 5", "Ch. 5"
    word_match = re.search(r'(?i)\b(?:episode|ep|part|chapter|ch)\.?\s*#?\s*(\d+)\b', text)
    if word_match:
        return int(word_match.group(1))

    # 3. Hash or direct E format: "#5", "#05", "E5"
    hash_match = re.search(r'(?i)(?:#|(?<=\b)E)(\d+)\b', text)
    if hash_match:
        return int(hash_match.group(1))

    return None

def check_video_matches_series(video, series):
    combined_text = f"{video['title']} {video['description']}".lower()

    # Exclude keywords check
    for ex in series.get("exclude_keywords", []):
        if ex.strip() and ex.strip().lower() in combined_text:
            print(f"  -> Discarded by exclude keyword '{ex}'")
            return False, None

    # Include keywords check (all include keywords must match)
    for inc in series.get("include_keywords", []):
        if inc.strip() and inc.strip().lower() not in combined_text:
            return False, None

    # Episode extraction: pehle title check karo, nahi mile toh description
    ep_num = extract_episode_number(video["title"])
    if ep_num is None:
        ep_num = extract_episode_number(video["description"])

    if ep_num is None:
        print(f"  -> Keywords matched, but no episode number detected in '{video['title']}'")
        return False, None

    last_watched = series.get("last_watched_episode", 0)
    if ep_num <= last_watched:
        print(f"  -> Detected Ep {ep_num} <= last watched {last_watched}. Skipping.")
        return False, None

    return True, ep_num

def main():
    if not os.path.exists(STATE_FILE):
        save_json(STATE_FILE, {})

    config = load_json(CONFIG_FILE, {"series": []})
    series_list = config.get("series", [])
    if not series_list:
        print("config.json mein koi series nahi mili!")
        return

    state = load_json(STATE_FILE, {})

    # Channel identification grouping
    channel_to_series = {}
    for s in series_list:
        ident = s.get("channel") or s.get("channel_id") or ""
        ident = ident.strip()
        if ident:
            channel_to_series.setdefault(ident, []).append(s)

    for ident, series_configs in channel_to_series.items():
        channel_id = resolve_to_channel_id(ident)
        if not channel_id:
            print(f"Skipping {ident}: Channel ID unresolvable.")
            continue

        print(f"\nChecking RSS feed for: {channel_id} ({ident})")
        videos = fetch_channel_feed(channel_id)
        if not videos:
            print(f"No videos found or feed empty for {channel_id}")
            continue

        # First run seed
        if channel_id not in state:
            print(f"First run for {channel_id}. Seeding {len(videos)} videos without alert.")
            state[channel_id] = [v["id"] for v in videos]
            save_json(STATE_FILE, state)
            continue

        seen_ids = set(state.get(channel_id, []))
        new_videos = [v for v in reversed(videos) if v["id"] not in seen_ids]

        if not new_videos:
            print(f"Channel {channel_id} is up to date.")
            continue

        print(f"Found {len(new_videos)} new video(s) for {channel_id}.")
        for vid in new_videos:
            print(f"\nEvaluating: '{vid['title']}' ({vid['id']})")
            
            matched = False
            for s in series_configs:
                is_match, ep_num = check_video_matches_series(vid, s)
                if is_match:
                    print(f"  MATCH FOUND! Series: {s['name']}, Detected Next Episode: {ep_num}")
                    msg = get_ai_message(s["name"], ep_num, vid["title"], vid["link"])
                    send_telegram_message(msg)
                    matched = True
                    break

            # Har processed video ko state mein save karenge taaki repeat check na ho
            state[channel_id].append(vid["id"])
            save_json(STATE_FILE, state)

if __name__ == "__main__":
    main()

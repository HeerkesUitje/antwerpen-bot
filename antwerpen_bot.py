import mimetypes
import json
import os
import random
import re
import html as html_lib
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

# ====== INSTELLINGEN ======
TRIP_DATE = date(2026, 11, 27)
LAT, LON = 51.2194, 4.4025
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID", None)
RSS_URL = "https://www.vrt.be/vrtnws/nl.rss.articles.xml"
PHOTO_DIR = Path(__file__).parent / "photos"

# Debug: check of CHAT_ID en BOT_TOKEN beschikbaar zijn
print(f"[DEBUG] CHAT_ID aanwezig: {'ja' if CHAT_ID else 'NEE'}")
print(f"[DEBUG] BOT_TOKEN aanwezig: {'ja' if BOT_TOKEN else 'NEE'}")

HISTORY_FLASHBACKS = [
    # ... je volledige HISTORY_FLASHBACKS-lijst hier, ongewijzigd ...
]

FACTS = [
    # ... je volledige FACTS-lijst hier, ongewijzigd ...
]

PUB_TIPS = [
    # ... je volledige PUB_TIPS-lijst hier, ongewijzigd ...
]

FOOD_TIPS = [
    # ... je volledige FOOD_TIPS-lijst hier, ongewijzigd ...
]

QUOTES_MORNING = [
    # ... je volledige QUOTES_MORNING-lijst hier, ongewijzigd ...
]

QUOTES_EVENING = [
    # ... je volledige QUOTES_EVENING-lijst hier, ongewijzigd ...
]


def get_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,apparent_temperature,precipitation"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=Europe%2FBrussels"
    )
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def get_antwerp_news():
    """Haalt VRT-nieuws op: Antwerps eerst, aanvullen met Vlaams nieuws tot 3 titels."""
    try:
        print("[DEBUG] Nieuwsfeed ophalen...")
        with urllib.request.urlopen(RSS_URL, timeout=10) as resp:
            xml_content = resp.read()

        print(f"[DEBUG] XML ontvangen: {len(xml_content)} bytes")

        # Regex die ook <title type="text"> matcht; behoud originele casing
        titles = []
        for match in re.finditer(r"<title[^>]*>([^<]+)</title>", xml_content.decode("utf-8", errors="ignore")):
            title = html_lib.unescape(match.group(1)).strip()
            if len(title) > 10 and "vrt nws:" not in title.lower():
                titles.append(title)

        print(f"[DEBUG] Totaal aantal titels gevonden: {len(titles)}")

        # Eerst Antwerps, aanvullen met algemeen Vlaams nieuws tot 3
        antwerp_titles = [t for t in titles if "antwerp" in t.lower()]
        overige = [t for t in titles if t not in antwerp_titles]
        nieuws_titels = (antwerp_titles + overige)[:3]

        print(f"[DEBUG] Antwerpse titels: {len(antwerp_titles)}, "
              f"eindselectie: {len(nieuws_titels)}")
        return nieuws_titels

    except Exception as e:
        print(f"[DEBUG] Nieuws ophalen MISLUKT: {e}")

    return []


def countdown_text(countdown):
    if countdown > 1:
        return f"Nog {countdown} nachtjes slapen! 🎉"
    elif countdown == 1:
        return "MORGEN GAAT HET GEBEURDEN! 🚀"
    return "HET IS ZORVER! 🎉🎉🎉"


def build_message(weather, news, countdown, is_evening):
    """Bouwt het bericht: beide edities hebben dezelfde onderdelen."""
    current = weather["current"]
    daily = weather["daily"]
    tip = random.choice(PUB_TIPS + FOOD_TIPS)

    if is_evening:
        kop = "\U0001F319 AVONDEDITIE — ANTWERPEN UPDATE"
        quote = random.choice(QUOTES_EVENING)
    else:
        kop = "\U0001F305 OCHTENDEDITIE — ANTWERPEN UPDATE"
        quote = random.choice(QUOTES_MORNING)

    parts = [
        kop,
        f"{'=' * 21}",
        "",
        countdown_text(countdown),
        "",
        f"\U000026C5 HET WEER",
        f"Nu {current['temperature_2m']:.0f}\u00B0C "
        f"(gevoel {current['apparent_temperature']:.0f}\u00B0C), "
        f"max {daily['temperature_2m_max'][0]:.0f}\u00B0C, "
        f"regenkans {daily['precipitation_probability_max'][0]}%",
        "",
    ]

    if news:
        parts += ["\U0001F4F0 NIEUWS"]
        for t in news:
            parts.append(f"• {t}")
        parts.append("")

    parts += [
        f"\U0001F4A1 FEITJE VAN DE DAG",
        f"{random.choice(FACTS)}",
        "",
        f"\U0001F37A TIP",
        f"{tip}",
        "",
        f"\U0001F4DC GESCHIEDENIS HERHAALT ZICH",
        f"{random.choice(HISTORY_FLASHBACKS)}",
        "",
        f"\U0001F44B {quote}",
    ]
    return "\n".join(parts)


def send_message(text, target_chat=None):
    chat = target_chat or CHAT_ID
    if not chat:
        print("[ERROR] Geen chat-ID bekend! Kan geen bericht sturen.")
        return False

    payload = json.dumps({"chat_id": chat, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    print(f"Telegram response: {result['ok']}")
    print(f"[DEBUG] Bericht verstuurd naar chat {chat}")
    return True


def send_photo(path, caption, target_chat=None):
    """Verstuurt een echte foto met bijschrift naar een chat."""
    chat = target_chat or CHAT_ID
    if not chat:
        print("[ERROR] Geen chat-ID bekend! Kan geen foto sturen.")
        return False

    boundary = "----AntwerpenBot123"
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        filedata = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{chat}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + filedata + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    print(f"Foto verzonden naar chat {chat}: {result['ok']}")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        is_evening = sys.argv[1].strip().lower() in ("avond", "evening")
    else:
        is_evening = datetime.now().hour >= 18

    countdown = (TRIP_DATE - date.today()).days
    weather = get_weather()
    news = get_antwerp_news()
    message = build_message(weather, news, countdown, is_evening)

    print(message)

    # Chat-lijst opbouwen: MULTI_CHAT_IDS + CHAT_ID als vangnet
    multi_raw = os.environ.get("MULTI_CHAT_IDS", "")
    print(f"[DEBUG] MULTI_CHAT_IDS ontvangen: {multi_raw!r}")
    try:
        chat_ids = json.loads(multi_raw) if multi_raw else []
    except Exception as e:
        print(f"[DEBUG] MULTI_CHAT_IDS is geen geldige JSON: {e}")
        chat_ids = []

    if CHAT_ID and CHAT_ID not in chat_ids:
        chat_ids.append(CHAT_ID)

    if not chat_ids:
        print("[ERROR] Geen chat-IDs geconfigureerd!")
    else:
        for cid in chat_ids:
            send_message(message, target_chat=str(cid))

    # Foto versturen — in beide edities
    photos = list(PHOTO_DIR.glob("*.jpg"))
    print(f"[DEBUG] Foto's gevonden: {len(photos)} in {PHOTO_DIR}")
    for p in photos:
        print(f"[DEBUG]   - {p.name}")

    if photos and chat_ids:
        foto = random.choice(photos)
        for cid in chat_ids:
            send_photo(str(foto), "📸 TERUGBLIK om bij vooruit te kijken :)", target_chat=str(cid))
    else:
        print("[DEBUG] GEEN foto verstuurd — check de foto-map!")

import json
import os
import random
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from zoneinfo import ZoneInfo

import antwerpen_bot as bot   # hergebruikt FACTS, get_weather, etc.

BOT_TOKEN = os.environ["BOT_TOKEN"]
FILES_FEED_URL = os.environ.get("FILES_FEED_URL", "")
OWNER_ID = 35520211   # Jouw Telegram-ID
FILES_KEYWORDS = ("Antwerpen", "Antwerp", "R1", "R2", "E19", "E313", "A12", "E34", "E17")

HELP_TEXT = (
    "Beschikbare commando's:\n"
    "/countdown — Nachtjes tot Antwerpen\n"
    "/feit — Leuk feitje over de stad\n"
    "/weer — Actueel weer in 't Stad\n"
    "/files — Verkeershinder rond R1/R2\n"
    "/nieuws — Actuele VRT-koppen\n"
    "/bug — Meld een probleem aan Stan\n"
    "/cafe — Random café-tip\n"
    "/eet — Random eettip\n"
)

def tg(method, payload):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

TYPE_NL = {
    "newRoadworksLayout": "nieuwe wegenindeling (werkzone)",
    "narrowLanes": "vernauwde rijstroken",
    "laneClosure": "rijstrook afgesloten",
    "roadworks": "wegenwerken",
    "intermittentShortTermRoadworks": "kortdurende wegenwerken",
    "roadMarkingWork": "wegmarkeringwerken",
    "resurfacing": "herstel wegdek",
    "singleAlternateLineTraffic": "om de beurt één rijstrook beschikbaar",
    "obstruction": "obstakel op de weg",
    "maintenanceWorks": "onderhoudswerken",
    "speedReduction": "verlaagde maximumsnelheid",
}

def _tag(elem):
    return elem.tag.split("}")[-1]

def get_antwerp_traffic():
    """DATEXII-feed: filtert situaties rond Antwerpen via Lambert 72-coördinaten."""
    if not FILES_FEED_URL:
        return "config_fout"

    try:
        req = urllib.request.Request(
            FILES_FEED_URL,
            headers={"User-Agent": "AntwerpenTripBot/1.0 (vriendengroep)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            tree = ET.fromstring(resp.read())

        # Lambert 72-boundingbox rond Antwerpen (R1, R2, havens, noord- en zuidrand)
        XMIN, XMAX = 138000, 164000
        YMIN, YMAX = 194000, 222000

        items = []
        for sit in tree.iter():
            if _tag(sit) != "situation":
                continue

            xs, ys = [], []
            for el in sit.iter():
                if _tag(el.tag) == "posList" and el.text:
                    try:
                        nums = [float(v) for v in el.text.split()]
                    except ValueError:
                        continue
                    xs += nums[0::2]
                    ys += nums[1::2]

            # Binnen de box rond Antwerpen?
            if not any(XMIN <= x <= XMAX and YMIN <= y <= YMAX for x, y in zip(xs, ys)):
                continue

            types, endtime = set(), None
            for el in sit.iter():
                t = (el.text or "").strip()
                if _tag(el) == "overallEndTime" and t:
                    endtime = t[:10]
                elif t and t[0].islower():          # enum-waarden zijn camelCase
                    types.add(TYPE_NL.get(t, t))

            if not types:
                types = {"melding"}

            for t in sorted(types):
                entry = "• " + t + (f" (loopt t/m {endtime})" if endtime else "")
                if entry not in items:
                    items.append(entry)

        print(f"[DEBUG] Antwerpse situaties gevonden: {len(items)}")
        return items[:5]

    except Exception as e:
        print(f"[DEBUG] Feed ophalen MISLUKT: {e}")
        return "fetch_fout"

def get_news():
    """VRT-nieuws: eerst Antwerpen, anders Vlaams."""
    with urllib.request.urlopen(bot.RSS_URL, timeout=10) as resp:
        tree = ET.fromstring(resp.read())
    items = tree.findall(".//item")
    antwerp = []
    general = []
    for i in items:
        title = (i.findtext("title") or "").strip()
        link = (i.findtext("link") or "").strip()
        if not title:
            continue
        desc = i.findtext("description") or ""
        entry = f"• {title}\n{link}"
        if "antwerp" in (title + desc).lower() and len(antwerp) < 5:
            antwerp.append(entry)
        if len(general) < 5:
            general.append(entry)
    if antwerp:
        return "\U0001F4F0 NIEUWS — REGIO ANTWERPEN\n\n" + "\n\n".join(antwerp[:3])
    if general:
        return "\U0001F4F0 NIEUWS — VLAANDEREN\n\n" + "\n\n".join(general[:3])
    return "Nieuwsdienst lijkt plat. Rustig land, Vlaanderen."

def answer(text):
    """Vertaalt commando naar antwoord."""
    cmd = text.strip().split()[0].split("@")[0].lower()

    if cmd == "/countdown":
        rest = (bot.TRIP_DATE - date.today()).days
        if rest > 1:
            return f"Nog {rest} nachtjes, meneer."
        if rest == 1:
            return "MORGEN GAAT HET GEBEURDEN. 🚀"
        if rest == 0:
            return "HET IS ZOVER. Waar blijf je? 🎉"
        return "Het weekend is geweest. Legendarisch. 🎲"

    if cmd == "/feit":
        return random.choice(bot.FACTS)

    if cmd == "/weer":
        w = bot.get_weather()
        c = w["current"]
        d = w["daily"]
        return f"☁️ Nu {c['temperature_2m']:.0f}°C (gevoel {c['apparent_temperature']:.0f}°C), max {d['temperature_2m_max'][0]:.0f}°C, regenkans {d['precipitation_probability_max'][0]}%"

    if cmd == "/files":
        hits = get_antwerp_traffic()
        if hits == "config_fout":
            return "Feed-URL is niet geconfigureerd in de secrets."
        if hits == "fetch_fout":
            return "Verkeersfeed kon niet worden opgehaald. Stan kijkt in de logs."
        if not hits:
            return "Geen meldingen rond Antwerpen. Uitzonderlijk rustig — of de sensoren slapen."
        return "\U0001F6A6 VERKEERSHINDER ROND ANTWERPEN\n\n" + "\n".join(f"• {h}" for h in hits)

    if cmd == "/nieuws":
        return get_news()

    if cmd == "/bug":
        return "🐞 Melding ontvangen.\n\nStan is geïnformeerd en kijkt er zo spoedig mogelijk naar.\nDe Heeren worden ondertussen verder ongestoord gelaten."

    if cmd == "/cafe":
        return f"🍻 TIP:\n{random.choice(bot.PUB_TIPS)}"

    if cmd == "/eet":
        return f"🍽️ TIP:\n{random.choice(bot.FOOD_TIPS)}"

    if cmd in ("/help", "/start"):
        return HELP_TEXT

    return None

def main():
    with urllib.request.urlopen(
        f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    ) as resp:
        data = json.loads(resp.read())

    updates = data.get("result", [])
    for upd in updates:
        msg = upd.get("message") or {}
        chat_id = msg.get("chat", {}).get("id")
        text = (msg.get("text") or "").strip()
        if not text.startswith("/") or chat_id is None:
            continue
        
        reply = answer(text)

        # Bug-melding: privé naar Stan
        if text.startswith("/bug"):
            sender = msg.get("from", {}).get("first_name", "Onbekend")
            ts = datetime.now(ZoneInfo("Europe/Brussels")).strftime("%H:%M")
            tg("sendMessage", {
                "chat_id": OWNER_ID,
                "text": f"🐞 BUG-MELDING van {sender} ({ts}):\n\n{text}",
            })

        if reply:
            tg("sendMessage", {
                "chat_id": chat_id,
                "text": reply,
                "reply_to_message_id": msg.get("message_id"),  # ← nieuw
            })
            print(f"Beantwoord: {text!r} in chat {chat_id}")

    if updates:
        last = updates[-1]["update_id"]
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last + 1}"
        )

if __name__ == "__main__":
    main()

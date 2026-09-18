import json
import os
import random
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from zoneinfo import ZoneInfo

import antwerpen_bot as bot   # hergebruikt FACTS, get_weather, etc.

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 35520211   # Jouw Telegram-ID

HELP_TEXT = (
    "Beschikbare commando's:\n"
    "/countdown — Nachtjes tot Antwerpen\n"
    "/feit — Leuk feitje over de stad\n"
    "/weer — Actueel weer in 't Stad\n"
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
    "trafficCongestion": "verkeersopstopping",
    "accident": "ongeval",
    "emergencyVehicle": "hulpvoertuig aanwezig",
    "roadClosed": "weg gesloten",
    "allLanesClosed": "alle rijstroken afgesloten",
}

def _tag(elem):
    return elem.tag.split("}")[-1]

def _local(tag):
    """Namespace strippen: '{http://...}entry' -> 'entry'"""
    return tag.rsplit('}', 1)[-1]

def get_news():
    """VRT-nieuws: eerst Antwerpen, anders Vlaams. Werkt voor RSS én Atom."""
    try:
        print("[DEBUG] Nieuwsfeed ophalen...")
        with urllib.request.urlopen(bot.RSS_URL, timeout=10) as resp:
            xml_content = resp.read()

        print(f"[DEBUG] XML ontvangen: {len(xml_content)} bytes")

        tree = ET.fromstring(xml_content)

        # Verzamel items/entries: werkt voor RSS (<item>) én Atom (<entry>)
        stories = []
        for node in tree.iter():
            if _local(node.tag) not in ("item", "entry"):
                continue
            title, link, desc = "", "", ""
            for child in node:
                ct = _local(child.tag)
                if ct == "title":
                    title = (child.text or "").strip()
                elif ct == "link":
                    # Atom: <link href="..."/>, RSS: <link>tekst</link>
                    link = ((child.get("href") or child.text or "")).strip()
                elif ct in ("description", "summary", "content"):
                    desc = (child.text or "").strip()
            if title:
                stories.append((title, link, desc))

        print(f"[DEBUG] Totaal aantal nieuws-items gevonden: {len(stories)}")

        antwerp = []
        general = []
        for idx, (title, link, desc) in enumerate(stories):
            entry = f"• {title}" + (f"\n{link}" if link else "")
            if idx < 10:
                print(f"[DEBUG] Item {idx+1}: {title[:80]}")

            combined = (title + " " + desc).lower()
            if any(k in combined for k in ["antwerpen", "antwerp"]) and len(antwerp) < 5:
                antwerp.append(entry)
                print(f"[DEBUG] ✓ Antwerps item gevonden: {title[:60]}")
            if len(general) < 5:
                general.append(entry)

        print(f"[DEBUG] Antwerpse items: {len(antwerp)}, Algemene items: {len(general)}")

        if antwerp:
            return "\U0001F4F0 NIEUWS — REGIO ANTWERPEN\n\n" + "\n\n".join(antwerp[:3])
        if general:
            return "\U0001F4F0 NIEUWS — VLAANDEREN\n\n" + "\n\n".join(general[:3])
        return "Nieuwsdienst lijkt plat. Rustig land, Vlaanderen."

    except Exception as e:
        print(f"[DEBUG] Nieuws ophalen MISLUKT: {e}")
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

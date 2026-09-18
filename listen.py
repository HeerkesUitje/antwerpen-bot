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
    "trafficCongestion": "verkeersopstopping",
    "accident": "ongeval",
    "emergencyVehicle": "hulpvoertuig aanwezig",
    "roadClosed": "weg gesloten",
    "allLanesClosed": "alle rijstroken afgesloten",
}

def _tag(elem):
    return elem.tag.split("}")[-1]

def get_antwerp_traffic():
    """DATEXII-feed: filtert situaties rond Antwerpen via Lambert 72-coördinaten."""
    if not FILES_FEED_URL:
        return "config_fout"

    import time
    xml_data = None
    for poging in range(3):
        try:
            req = urllib.request.Request(
                FILES_FEED_URL,
                headers={"User-Agent": "AntwerpenTripBot/1.0 (vriendengroep)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read()
            break   # gelukt, uit de herhalingslus
        except Exception as e:
            print(f"[DEBUG] Poging {poging + 1} mislukt: {e}")
            time.sleep(10)   # even ademhalen en nog eens proberen

    if xml_data is None:
        return "fetch_fout"

    try:
        tree = ET.fromstring(xml_data)

        # Lambert 72-boundingbox rond Antwerpen (R1, R2, havens, noord- en zuidrand)
        XMIN, XMAX = 138000, 164000
        YMIN, YMAX = 194000, 222000

        items = []
        for sit in tree.iter():
            if _tag(sit) != "situation":
                continue

            xs, ys = [], []
            for el in sit.iter():
                t = _tag(el)
                if t == "posList" and el.text:
                    try:
                        nums = [float(v) for v in el.text.split()]
                        xs += nums[0::2]
                        ys += nums[1::2]
                    except ValueError:
                        continue

            # Binnen de box rond Antwerpen?
            if not any(XMIN <= x <= XMAX and YMIN <= y <= YMAX for x, y in zip(xs, ys)):
                continue

            # Zoek de verkeerstypes uit specifieke tags
            types, endtime = [], None
            for el in sit.iter():
                tagname = _tag(el)
                t = (el.text or "").strip()

                if tagname == "overallEndTime" and t:
                    endtime = t[:10]
                elif tagname in ("roadOrCarriagewayOrLaneManagementType", 
                                "abnormalTrafficType",
                                "trafficSourceType",
                                "genericSituationType"):
                    if t and t in TYPE_NL:
                        types.append(TYPE_NL[t])

            if not types:
                continue  # Skip situaties zonder type

            for t in sorted(set(types)):
                entry = "• " + t + (f" (loopt t/m {endtime})" if endtime else "")
                if entry not in items:
                    items.append(entry)

        return items[:5] if items else []

    except Exception as e:
        print(f"[DEBUG] Feed ophalen MISLUKT: {e}")
        return "fetch_fout"

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

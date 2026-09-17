import json
import os
import random
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

import antwerpen_bot as bot   # hergebruikt FACTS, get_weather, etc.

BOT_TOKEN = os.environ["BOT_TOKEN"]
FILES_FEED_URL = os.environ.get("FILES_FEED_URL", "")

FILES_KEYWORDS = (
    "Antwerpen", "Antwerp", "R1", "R2", "E19", "E313", "A12",
    "Waasland", "Willebroek", "Lokeren", "Brecht",
)

HELP_TEXT = (
    "Beschikbare commando's:\n"
    "/countdown — nachtjes tot Antwerpen\n"
    "/feit — weetje over de stad\n"
    "/weer — actueel weer in 't Stad\n"
    "/files — verkeershinder rond Antwerpen"
)


def tg(method, payload):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_antwerp_traffic():
    """Haalt DATEXII-feed op en filtert meldingen rond Antwerpen."""
    if not FILES_FEED_URL:
        return None
    with urllib.request.urlopen(FILES_FEED_URL, timeout=15) as resp:
        tree = ET.fromstring(resp.read())
    hits = []
    for elem in tree.iter():
        text = (elem.text or "").strip()
        if len(text) > 20 and any(k in text for k in FILES_KEYWORDS):
            if text not in hits:
                hits.append(text)
    return hits[:5]


def answer(text):
    """Vertaalt een commando naar een antwoord (of None)."""
    cmd = text.strip().split()[0].split("@")[0].lower()

    if cmd == "/countdown":
        rest = (bot.TRIP_DATE - date.today()).days
        if rest > 1:
            return f"Nog {rest} nachtjes, meneer."
        if rest == 1:
            return "MORGEN GAAT HET GEBEURDEN. \U0001F680"
        if rest == 0:
            return "HET IS ZOVER. Waar blijf je? \U0001F389"
        return "Het weekend is geweest. Legendarisch. \U0001F3B2"

    if cmd == "/feit":
        return random.choice(bot.FACTS)

    if cmd == "/weer":
        w = bot.get_weather()
        c = w["current"]
        d = w["daily"]
        return (
            f"\u2601 Nu {c['temperature_2m']:.0f}\u00B0C "
            f"(gevoel {c['apparent_temperature']:.0f}\u00B0C), "
            f"max {d['temperature_2m_max'][0]:.0f}\u00B0C, "
            f"regenkans {d['precipitation_probability_max'][0]}%"
        )

    if cmd == "/files":
        hits = get_antwerp_traffic()
        if hits is None:
            return "Geen verkeersfeed geconfigureerd. (Zie FILES_FEED_URL.)"
        if not hits:
            return "Geen meldingen rond Antwerpen. Uitzonderlijk rustig — of de sensoren slapen."
        return "\U0001F6A6 VERKEERSHINDER ROND ANTWERPEN\n\n" + "\n".join(f"• {h}" for h in hits)

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
        if reply:
            tg("sendMessage", {"chat_id": chat_id, "text": reply})
            print(f"Beantwoord: {text!r} in chat {chat_id}")

    if updates:
        # Bevestig verwerking: oudere updates worden server-side weggegooid,
        # zodat de volgende run alleen nieuwe berichten ziet.
        last = updates[-1]["update_id"]
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last + 1}"
        )


if __name__ == "__main__":
    main()

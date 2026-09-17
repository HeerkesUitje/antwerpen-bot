import json
import os
import random
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime

# ====== INSTELLINGEN ======
TRIP_DATE = date(2026, 11, 27)   # <-- echte datum van jullie weekend!
LAT, LON = 51.2194, 4.4025
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
RSS_URL = "https://www.vrt.be/vrtnws/nl.rss.articles.xml"

EVENING_HOUR = 16   # na 16:00 NL-tijd geldt het bericht als avondeditie

FACTS = [
    "Het Centraal Station werd in 2009 uitgeroepen tot het mooiste treinstation ter wereld.",
    "Antwerpen heeft de oudste dierentuin van Europa: de ZOO van 1843.",
    "De haven van Antwerpen is de tweede grootste van Europa.",
    "Rubens woonde hier — zijn huis is nu een prachtig museum.",
    "Antwerpen is de diamantstad: 84% van 's werelds ruwe diamanten passeert hier.",
    "Het woord 'handswerpen' (hand werpen) zou de oorsprong van de naam zijn.",
    "De Onze-Lieve-Vrouwetoren is de hoogste kerktoren van de Lage Landen.",
    "De Sint-Annatunnel onder de Schelde is een Art-Deco juweeltje.",
    "In 't Zuid huizen de meeste galeries en vintage winkels van de stad.",
    "Op de Groenplaats stond ooit het Sint-Elisabethziekenhuis; nu staat er Rubens.",
]

# Wekelijkse thema's, automatisch gekozen op basis van de countdown
THEMES = {
    4: ("🏛️ GESCHIEDENIS WEEK", "Van Rubens tot de Schelde-legende van Brabo."),
    3: ("🍺 UITGAAN WEEK", "Cafés, bier en nachtelijke avonturen in 't Stad."),
    2: ("🍽️ ETEN WEEK", "Frietjes, stoofvlees, frikandellen. De échte haute cuisine."),
    1: ("🧳 PRAKTISCHE WEEK", "Tassen pakken, regelen, aftellen."),
    0: ("🚂 HET IS ZOVER", "Geen intro's meer nodig. Gaan!"),
}

PUB_TIPS = [
    "Café Bourla: klassiek, pal naast de Bourla-schouwburg.",
    "'t Waagstuk: eetcafé met stoofvlees om thuis van te dromen.",
    "Kulminator: meer dan 700 bieren en meubilair uit oma's tijd.",
    "De Vagant: klein, bruin café — binnengaan zonder afspraak is sport.",
    "Café De Leeuw: Antwerps, lokaal, geen poespas.",
    "Bar Léon op de Leopoldplaats: chic broodje/lunch-plek.",
]

FOOD_TIPS = [
    "Frituur n°1 van Antwerpen — vraag de locals welke dat is. Discussies gegarandeerd.",
    "Frites Atnoon bij het Centraal Station: vers uit de frituur.",
    "Fish a'gogo: visgerechten met een ziel, vlak bij de kaaien.",
    "Exki is toeristenvoer. Skip. Ga voor een echt frituur.",
    "Balls & Glory op de Kloosterstraat: gehaktballen als kunstvorm.",
]

QUOTES_MORNING = [
    "Goedemorgen — de koffie smaakt beter met een countdown.",
    "Nog even doorbijten, het bier wacht.",
    "Vandaag is ook weer een dag dichter bij Antwerpen.",
    "Wie doet er al afwaswerk voor de koelbox?",
]

QUOTES_EVENING = [
    "Vanavond borrel je ergens anders. Zonde.",
    "Nog X nachtjes — euh sorry, nog even volhouden.",
    "Droom maar lekker van handjes en frietjes.",
    "De barman van je dromen heet Boris en schenkt Westmalle.",
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
    """Haalt VRT-nieuws op en filtert op artikelen over Antwerpen."""
    try:
        with urllib.request.urlopen(RSS_URL, timeout=10) as resp:
            tree = ET.fromstring(resp.read())
        items = tree.findall(".//item")
        hits = [
            (i.findtext("title", "").strip(), i.findtext("link", "").strip())
            for i in items
            if "antwerp" in (i.findtext("title", "") + i.findtext("description", "")).lower()
        ]
        if hits:
            return random.choice(hits)
    except Exception as e:
        print(f"Nieuws ophalen mislukt: {e}")
    return None


def send_message(text):
    payload = json.dumps({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    print(f"Telegram response: {result['ok']}")


def pick_theme(countdown_days):
    weeks_left = max(0, -(-countdown_days // 7))   # afronden naar boven
    if countdown_days <= 0:
        return THEMES[0]
    return THEMES.get(min(weeks_left, 4))


def build_morning(weather, news, theme, countdown):
    current = weather["current"]
    daily = weather["daily"]
    if countdown > 1:
        countdown_text = f"Nog {countdown} nachtjes slapen! \U0001F389"
    elif countdown == 1:
        countdown_text = "MORGEN GAAT HET GEBEURDEN! \U0001F680"
    else:
        countdown_text = "HET IS ZOVER! \U0001F389\U0001F389\U0001F389"

    parts = [
        f"\U0001F305 OCHTENDEDITIE — ANTWERPEN UPDATE",
        f"{'=' * 21}",
        f"",
        f"{theme[0]}: {theme[1]}",
        f"",
        f"{countdown_text}",
        "",
        f"\U000026C5 HET WEER",
        f"Nu {current['temperature_2m']:.0f}\u00B0C "
        f"(gevoel {current['apparent_temperature']:.0f}\u00B0C), "
        f"max {daily['temperature_2m_max'][0]:.0f}\u00B0C, "
        f"regenkans {daily['precipitation_probability_max'][0]}%",
        "",
        f"\U0001F4A1 FEITJE VAN DE DAG",
        f"{random.choice(FACTS)}",
    ]

    if news:
        parts += ["", f"\U0001F4F0 ANTWERPS NIEUWS", f"{news[0]}"]

    parts += ["", f"\U0001F44B {random.choice(QUOTES_MORNING)}"]
    return "\n".join(parts)


def build_evening(weather, theme, countdown):
    current = weather["current"]
    tip = random.choice(PUB_TIPS + FOOD_TIPS)
    parts = [
        f"\U0001F319 AVONDEDITIE — ANTWERPEN UPDATE",
        f"{'=' * 21}",
        f"",
        f"{theme[0]}: {theme[1]}",
        f"",
        f"\U0001F37A TIP VAN DE AVOND",
        f"{tip}",
        "",
        f"\U0001F327 FEITJE VAN DE DAG",
        f"{random.choice(FACTS)}",
        "",
        f"\U0001F44B {random.choice(QUOTES_EVENING)}",
    ]
    return "\n".join(parts)

def send_photo(path, caption):
    """Verstuurt een echte foto met bijschrift naar de groep."""
    boundary = "----AntwerpenBot123"
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        filedata = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{CHAT_ID}\r\n"
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
    print(f"Foto verzonden: {result['ok']}")
    
if __name__ == "__main__":
    now = datetime.now().hour
    is_evening = int(sys.argv[1]) >= EVENING_HOUR if len(sys.argv) > 1 else now >= 18
    countdown = (TRIP_DATE - date.today()).days
    theme = pick_theme(countdown)
    weather = get_weather()

    if is_evening:
        message = build_evening(weather, theme, countdown)
    else:
        news = get_antwerp_news()
        message = build_morning(weather, news, theme, countdown)

    print(message)
    send_message(message)
    photos = glob.glob("*.jpg")
    if photos and random.random() < 0.5:   # 50% kans op een terugblik-foto
        send_photo(random.choice(photos), "📸 TERUGBLIK — eentje uit de oude doos :)")

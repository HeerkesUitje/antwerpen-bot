import glob
import mimetypes
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

HISTORY_FLASHBACKS = [
    "1576: de Spaanse Furie. Antwerpen geplunderd, honderden doden. Nooit excuses gekregen.",
    "1584-85: het Beleg van Antwerpen. Vijf maanden volgehouden, toen Parma de Schelde dichtgooide. 400 jaar klagen over de tol daarna. Klagen is hier een ambacht.",
    "1609: Plantijn drukte al boeken voor half Europa. De eerste die bewees dat Antwerpen commercieel noch cultureel terugdeinst voor een monopoliepositie.",
    "1662: een speculant steekt de Stadsbibliotheek in brand. Begrafenisstoet, goud en zilver, alles ging in vlammen op.",
    "1794-95: de Fransen nemen de haven, de antifranse patriottenclaim zakt in. Twee eeuwen later doen bankiers in diamant nog steeds zaken in drie talen tegelijk.",
    "1830: de Belgen schudden de Hollanders af. De Schelde eindelijk tol-vrij. Rotterdam heeft het ze nooit vergeven.",
    "1894-1905: het Centraal Station wordt gebouwd bovenop een verdieping sloopwerk. Categorie 'ambitie boven functionaliteit' was toen al uitgevonden.",
    "1914: het Belgische leger verschanst zich rond Antwerpen, kijkt toe hoe de Duitsers oprukken. Uiteindelijk weg. Zonder verlies, zonder winst. Typisch gematigd België.",
    "1940: Vliegtuigbommen op Antwerpen, mei 1940. Even later volgt het park. De wederopbouw nam 20 jaar. Niets nieuws onder de Schelde-zon.",
    "1944-45: V-bommen op Antwerpen raken meer dan 5.000 burgers. Havenhouders bleven. Antwerpen bleef. Dat mag gezegd worden.",
    "1920: de Olympische Spelen in Antwerpen, inclusief rugslagzwemmen en zwak eetfestijn. Nadien: wereldverbeteraars, betere atleten, en 106 jaar discussie.",
]

FACTS = [
    "Categorietje 'hè, leeft die nog?!': Rubens. Sinds 1640. Nog steeds niet tegen te houden.",
    "Antwerpen viel in 1585, en de Amsterdamse zakenwereld heeft sindsdien een dankbriefje tegoed. Sommige dingen veranderen nooit.",
    "De ZOO van Antwerpen bestaat sinds 1843. Dat was van onze markten nog lang niet verbrand.",
    "84% van 's werelds ruwe diamanten passeert Antwerpen. Verzorger van de Rijnlandse economie, sinds eeuwen.",
    "De Onze-Lieve-Vrouwetoren: 123 meter, al 500 jaar hoogste kerktoren van de Lage Landen. Zonder één stremming.",
    "Categorietje 'Sommige dingen veranderen nooit': de prijs van een Duvel in het Grand Café van Antwerpen.",
    "De haven van Antwerpen is de op één na grootste van Europa. Rotterdam staat eerste, maar daar praten we vanavond niet over.",
    "Brabo wierp de reuzenhand in de Schelde. Waarschijnlijk de oudste geregistreerde testcase van 'handhaven'.",
    "Antwerpen verwelkomde in de jaren '70 de hippie-scene, maar de stad overleefde dat keurig. Zoals alles.",
    "Er is in Antwerpen ooit een grootschalige overstroming geweest in de 16e eeuw. Ook toen werd de spoor'service' niet beter.",
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
    "Goedemorgen. Nog even doorbijten, het bier wacht.",
    "Vandaag is het transatlantische nieuws waarschijnlijk weer debiel, maar wij gaan naar Antwerpen!",
    "Sommige dingen veranderen nooit. Gelukkig het bier ook niet.",
    "Vandaag is ook weer een dag dichter bij iets dat de moeite waard is.",
    "Wie heeft er al gecheckt of Pim nog leeft? Categorietje onderweg.",
    "Is Machiel al hardlopend vertrokken? Wie checkt zijn tussentijden?",
    "Erik: check je even je navigatie dat je niet naar Brugge rijdt ;-)",
    "JP: we zitten vlakbij water. Ik houd je handje wel vast ;-)",
    "Goedemorgen! Zijn de eitjes al gebakken, Anton?",
]

QUOTES_EVENING = [
    "Vanavond borrel je ergens anders. Geen BOB nodig.",
    "Nog X nachtjes — euh sorry, nog even volhouden.",
    "Droom maar lekker van handjes en frietjes.",
    "De barman van je dromen heet Guy en schenkt Westmalle.",
    "Heeft iemand al gecheckt of June Peers in de stad is?",
    "Be less like Tom Waes: biertje bij aankomst, niet onderweg!",
    "Helaas bestaat de Zillion niet meer, maar we kunnen vast ergens anders feesten!",
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
    ]
    parts += [
        "",
        "\U0001F4DC EEN GESCHIEDENISWEETJE",
        random.choice(HISTORY_FLASHBACKS),
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

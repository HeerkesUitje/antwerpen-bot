import json
import os
import random
import urllib.request
from datetime import date

# ====== INSTELLINGEN ======
TRIP_DATE = date(2026, 11, 27)   # aangepast
LAT, LON = 51.2194, 4.4025       # Antwerpen
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FACTS = [
    "Het Centraal Station werd in 2009 uitgeroepen tot het mooiste treinstation ter wereld.",
    "Antwerpen heeft de oudste dierentuin van Europa: de ZOO van 1843.",
    "De haven van Antwerpen is de tweede grootste van Europa.",
    "Rubens woonde hier — zijn huis is nu een prachtig museum.",
    "Antwerpen is de diamantstad: 84% van 's werelds ruwe diamanten passeert hier.",
    "Het woord 'handswerpen' (hand werpen) zou de oorsprong van de naam Antwerpen zijn.",
    "De Onze-Lieve-Vrouwetoren is al eeuwenlang de hoogste kerktoren van de Lage Landen.",
    "In 't Zuid huizen de meeste galeries en vintage winkels van de stad.",
    "Antwerpse frietjes met stoofvlees is praktisch een religie.",
    "De Sint-Annatunnel (voetgangerstunnel onder de Schelde) is een Art-Deco juweeltje.",
]

QUOTES = [
    "Straks Gent, straks Leuven, straks Antwerpen!",
    "Kofferbak vol verwachtingen.",
    "Nog even doorbijten, het bier wacht.",
    "Countdown loopt — wie doet er al afwaswerk voor de koelbox?",
]


def get_weather():
    """Haalt actuele weer voor Antwerpen op bij Open-Meteo (gratis, geen API key)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,apparent_temperature,precipitation"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=Europe%2FBrussels"
    )
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return data


def send_message(text):
    """Verstuurt een bericht naar de Telegram-groep."""
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    print(f"Telegram response: {result['ok']}")


def build_message(weather):
    countdown = (TRIP_DATE - date.today()).days
    fact = random.choice(FACTS)
    quote = random.choice(QUOTES)

    current = weather["current"]
    daily = weather["daily"]

    if countdown > 1:
        countdown_text = f"Nog maar {countdown} nachtjes slapen tot Antwerpen! \U0001F389"
    elif countdown == 1:
        countdown_text = "MORGEN GAAT HET GEBEURDEN! \U0001F680"
    elif countdown == 0:
        countdown_text = "HET IS ZOVER! \U0001F389\U0001F389\U0001F389"
    else:
        countdown_text = "We zijn er weer geweest — legendarisch weekend. \U0001F3B2"

    message = (
        f"\U0001F552 ANTWERPEN UPDATE\n"
        f"=====================\n\n"
        f"{countdown_text}\n\n"
        f"\U000026C5 HET WEER VANDAAG\n"
        f"Nu: {current['temperature_2m']:.0f}\u00B0C "
        f"(gevoels temperatuur {current['apparent_temperature']:.0f}\u00B0C)\n"
        f"Vandaag max {daily['temperature_2m_max'][0]:.0f}\u00B0C, "
        f"min {daily['temperature_2m_min'][0]:.0f}\u00B0C, "
        f"regenkans {daily['precipitation_probability_max'][0]}%\n\n"
        f"\U0001F4A1 FEITJE OVER ANTWERPEN\n"
        f"{fact}\n\n"
        f"\U0001F44B TOT BINNENKORT\n"
        f"{quote}"
    )
    return message


if __name__ == "__main__":
    weather = get_weather()
    message = build_message(weather)
    print(message)
    send_message(message)

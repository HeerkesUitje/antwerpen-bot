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
PHOTO_DIR = Path(__file__).parent  # repo-root: hier liggen de foto's

# Debug: check of CHAT_ID en BOT_TOKEN beschikbaar zijn
print(f"[DEBUG] CHAT_ID aanwezig: {'ja' if CHAT_ID else 'NEE'}")
print(f"[DEBUG] BOT_TOKEN aanwezig: {'ja' if BOT_TOKEN else 'NEE'}")

HISTORY_FLASHBACKS = [
  # --- Gouden eeuw & val (16e eeuw) ---
    "FLASHBACK [ca. 1540-1580]: In de 16e eeuw was Antwerpen de rijkste stad ten noorden van de Alpen.",
    "FLASHBACK [1560]: Rond 1560 telde de stad circa 100.000 inwoners - een wereldstad naar toenmalige maatstaven.",
    "FLASHBACK [16e eeuw]: Tijdgenoten noemden Antwerpen 'het Florence van het Noorden'.",
    "FLASHBACK [1531]: In 1531 opende in Antwerpen 's werelds eerste speciaal gebouwde effectenbeurs.",
    "FLASHBACK [1571-1602]: De Antwerpse beurs diende als voorbeeld voor de Royal Exchange in Londen (1571) en de beurs van Amsterdam (1602).",
    "FLASHBACK [ca. 1560]: Na Venetië was Antwerpen in de 16e eeuw de grootste drukkersstad van Europa.",
    "FLASHBACK [16e eeuw]: Antwerpen was in de 16e eeuw de suikerraffinagehoofdstad van Europa.",
    "FLASHBACK [1549-1589]: Christoffel Plantijn was de grootste drukker van zijn tijd; zijn meertalige Biblia Regia drukte hij in opdracht van koning Filips II van Spanje.",
    "FLASHBACK [1566]: De Beeldenstorm van 1566 trof Antwerpen het hardst: op één dag verdween een groot deel van de kerkkunst.",
    "FLASHBACK [1576]: In 1576 plunderden muitende Spaanse soldaten de stad: de Spaanse Furie.",
    "FLASHBACK [17-08-1585]: Op 17 augustus 1585 viel Antwerpen in Spaanse handen - het einde van de gouden eeuw van de stad.",
    "FLASHBACK [1585-1795]: Na de val blokkeerden de (nu Noord-)Nederlanden de Schelde, de slagader van de Antwerpse economie.",
    "FLASHBACK [1585-1590]: Ruim de helft van de bevolking vertrok na 1585 uit de stad.",
    "FLASHBACK [ca. 1590-1620]: Antwerpse kooplieden, bankiers en ambachtslieden hielpen Amsterdam opbouwen tot wereldstad.",
    "FLASHBACK [1648]: De Vrede van Münster (1648) verankerde de sluiting van de Schelde in een verdrag.",

    # --- Wederopstanding van de haven (1800-1900) ---
    "FLASHBACK [1803]: Napoleon bezocht de stad in 1803 en liet de eerste moderne dokken graven.",
    "FLASHBACK [ca. 1812]: Het Bonapartedok draagt nog altijd de naam van Napoleon.",
    "FLASHBACK [1863]: Pas in 1863 kocht België de Scheldetol van Nederland af - de rivier stroomde eindelijk vrij.",
    "FLASHBACK [1863-1900]: Na 1863 groeide Antwerpen binnen enkele decennia uit tot een wereldhaven.",

    # --- 20e eeuw ---
    "FLASHBACK [1914]: In 1914 trok het Belgische leger zich terug in de versterkte 'nationale redoute' Antwerpen.",
    "FLASHBACK [1930]: In 1930 organiseerde Antwerpen een wereldtentoonstelling.",
    "FLASHBACK [1933]: In 1933 opende het Sportpaleis, aanvankelijk als wielervelodroom.",
    "FLASHBACK [1944-1945]: In de Tweede Wereldoorlog werd Antwerpen harder door V-bommen getroffen dan enige andere stad.",
    "FLASHBACK [1944]: De Slag om de Schelde (1944) werd uitgevochten om de bevoorrading via de haven veilig te stellen.",
    "FLASHBACK [1993]: In 1993 was Antwerpen Culturele Hoofdstad van Europa.",

    # --- Recente geschiedenis & economie ---
    "FLASHBACK [2022]: In 2022 fuseerden de havens van Antwerpen en Zeebrugge tot de Haven van Antwerpen-Brugge.",
    "FLASHBACK [13e eeuw-1820]: In het Steen zat eeuwenlang een gevangenis.",
    "FLASHBACK [ca. 2025, schatting]: De haven vertegenwoordigt naar schatting zo'n 4 tot 5% van het Belgische bbp.",
    "FLASHBACK [ca. 2025, schatting]: De haven genereert ruim 60.000 directe banen en een veelvoud aan indirecte.",

    # --- Diamantgeschiedenis ---
    "FLASHBACK [sinds 1447]: Antwerpen is al sinds de 15e eeuw hét centrum van de wereldwijde diamanthandel.",
    "FLASHBACK [ca. 2012-2022]: Historisch passeerde circa 84% van alle ruwe diamanten ter wereld Antwerpen - dat aandeel daalt sinds de sancties tegen Rusland.",
    "FLASHBACK [2025]: In 2025 bedroeg de totale Antwerpse diamanthandel nog 19,07 miljard dollar (AWDC).",
    "FLASHBACK [2025]: Gepolijste diamanten vormden in 2025 zo'n 65% van de Antwerpse diamantexport.",
    "FLASHBACK [2024]: Sinds 1 januari 2024 zijn Russische diamanten verboden - dat kostte Antwerpen circa 30% van de ruwe import (AWDC).",
    "FLASHBACK [ca. 2017]: Het Diamantkwartier telt circa 1.500 bedrijven en honderden ateliers.",
    "FLASHBACK [1873-1934]: De Red Star Line (1873-1934) vervoerde arme Europeanen via Antwerpen naar de Nieuwe Wereld.",
]

FACTS = [
    # --- Legende & symbool ---
    "De naam Antwerpen komt volgens de legende van 'hand werpen': de Romeinse held Silvius Brabo wierp de hand van de reus Antigoon in de Schelde.",
    "De reus Antigoon eiste tol op de Schelde en hakte wanbetalers de hand af - tot Brabo hem versloeg.",
    "De Brabofontein op de Grote Markt toont exact dat moment: Brabo die de hand wegwerpt.",
    "De Antwerpse hand is hét streekproduct van de stad: je krijgt ze als koekje én als chocolade.",
    "Lange Wapper is de folkloristische reus van de stad; hij verschijnt vooral 's nachts en houdt slapers uit hun bed.",
    "Bij Het Steen staat het standbeeld van de Lange Wapper, gemaakt door beeldhouwster Albert Poels.",
    "'A Dog of Flanders', het verhaal van Nello en Patrasche, is in België vrijwel onbekend - maar enorm groot in Japan.",
    "In Japan staan standbeelden voor Nello en Patrasche, en er bestaat zelfs een animatieserie over hen.",
    "Antwerpenaren heten 'sinjoren', naar de Spaanse señores die in de 16e eeuw door de stad paradeerden.",
    "Rubens was lid van de Sint-Jorisgilde, de kruisboogschutters van de stad - schilderen was zijn vak, schieten zijn hobby.",

    # --- Architectuur & monumenten ---
    "De Onze-Lieve-Vrouwekathedraal heeft met 123 meter de hoogste kerktoren van de Benelux.",
    "De kathedraal is de grootste gotische kerk van de Lage Landen.",
    "In de kathedraal hangt de 'Kruisafdoening' van Rubens - zijn beroemdste triptiek.",
    "Er hangen in totaal vier Rubens-meesterwerken in één en dezelfde kerk.",
    "Het Centraal Station wordt de 'Spoorwegkathedraal' genoemd.",
    "Het stationsgebouw dateert van 1905.",
    "Het Centraal Station wordt internationaal herhaaldelijk uitgeroepen tot een van de mooiste treinstations ter wereld.",
    "Onder de grote koepel van Centraal Station liggen treinsporen op vier verschillende niveaus boven elkaar.",
    "De Grote Markt is omringd door pronkzige 16e-eeuwse gildenhuizen.",
    "Het Stadhuis van Antwerpen (1565) is een hoogtepunt van de Vlaamse renaissance.",
    "In Zurenborg staat de grootste concentratie art nouveau van België.",
    "De Cogels-Osylei is een openluchtmuseum van art nouveau.",
    "De Boerentoren (1931, 87 meter) geldt als de oudste wolkenkrabber van Europa.",
    "De Stadsfeestzaal (1908) brandde in 2000 bijna volledig af en is nu een luxueus winkelpaleis.",
    "Museum MAS (2011) is een toren van rode zandsteen die doet denken aan gestapelde containers.",
    "Op het dak van het MAS is het panorama over stad en haven gratis toegankelijk.",
    "Het Koninklijk Museum voor Schone Kunsten heropende in 2022 na een elf jaar durende restauratie.",
    "Het KMSKA bezit een van de grootste Rubens-collecties ter wereld.",
    "Met zijn immense koepel is het Justitiepaleis een van de grootste gerechtsgebouwen ter wereld.",
    "In de Sint-Annatunnel (1933) draaien nog altijd originele houten roltrappen - monumentaal erfgoed in functie.",
    "De Bourla is het laatste bewaarde romantische stadstheater van België.",
    "De Zoo van Antwerpen (1843) is de oudste dierentuin van België.",
    "De zoo ligt direct naast Centraal Station: van perron naar olifant in vijf minuten.",
    "De Vlaaikensgang is een verborgen middeleeuws steegje met huisjes - Antwerpens geheimste plek.",
    "De Red Star Line-gebouwen herbergen sinds 2013 het emigratiemuseum van de stad.",
    "Het Steen is het oudste gebouw van de stad, daterend uit het begin van de 13e eeuw.",
    "Het Havenhuis van Zaha Hadid lijkt een vliegende schotel bovenop een monumentaal gebouw uit 1922.",
    "De Sint-Pauluskerk heeft de rijkste barokke collectie van de stad, waaronder veel Rubens-copij.",
    "In de Sint-Jacobskerk ligt Rubens zelf begraven, vlak bij het altaar van zijn eigen kapel.",

    # --- Kunst, wetenschap & cultuur ---
    "Rubens woonde en werkte ruim veertig jaar in Antwerpen.",
    "Hij ontwierp zijn eigen woning aan de Wapper als een soort Italiaans palazzo.",
    "Rubens was niet alleen schilder maar ook diplomaat in Europese dienst.",
    "Hij werd door zowel de Engelse als de Spaanse kroon geridderd.",
    "Anthony van Dyck was de beroemdste leerling van Rubens.",
    "Pieter Bruegel de Oude woonde en werkte in Antwerpen.",
    "Jacob Jordaens bleef zijn hele leven in de stad - en weigerde pertinent om naar Italië te gaan.",
    "In het Plantin-Moretusmuseum staan de oudste bewaarde drukpersen ter wereld.",
    "Het Plantin-Moretusmuseum stond als eerste museum ter wereld op de Unesco-Werelderfgoedlijst.",
    "De Koninklijke Academie voor Schone Kunsten (1663) behoort tot de oudste kunstacademies ter wereld.",
    "De Antwerp Six veroorzaakten in 1986 een revolutie in de Londense modewereld.",
    "Tot de Antwerp Six behoorden Dries Van Noten en Ann Demeulemeester.",
    "In de Nationalestraat vind je de vlaggenschipwinkels van de Antwerpse mode.",
    "MoMu is het modemuseum van de stad.",
    "Panamarenko, de surrealistische luchtschipkunstenaar, was een Antwerpenaar.",
    "Marcel Broodthaers, kunstenaar en dichter, werd in Antwerpen geboren.",
    "Suske en Wiske-tekenaar Willy Vandersteen werd in Antwerpen geboren.",
    "Schrijver Tom Lanoye is een uitgesproken sinjoor.",
    "De Red Star Line vervoerde ruim twee miljoen Europeanen naar de Verenigde Staten.",
    "Het Middelheimmuseum is een gratis beeldenpark in het groen van de stad.",
    "Modehuis Dries Van Noten houdt winkel in een statig pand aan de Nationalestraat, compleet met binnentuin.",
]

PUB_TIPS = [
    "Café Bourla: klassiek, pal naast de Bourla-schouwburg.",
    "'t Waagstuk: eetcafé met stoofvlees om thuis van te dromen.",
    "Kulminator: meer dan 700 bieren en meubilair uit oma's tijd.",
    "De Vagant: klein, bruin café — binnengaan zonder afspraak is sport.",
    "Café De Leeuw: Antwerps, lokaal, geen poespas.",
    "Bar Léon op de Leopoldplaats: chic broodje/lunch-plek.",
    "Den Engel: authentiek Antwerps café op de Grote Markt, Koninck uit een convexglas met terraszicht op het plein.",
    "Café Pelikaan: 4.6/5 op TripAdvisor, bruine sfeer met lokale clientèle.",
    "Café Cabron: 'cool pub' vlakbij de Onze-Lieve-Vrouwekathedraal, authentieke sfeer.",
    "Café Pardaf: beer bar dichtbij de Grote Markt en de Schelde, altijd een bezoek waard volgens reizigers.",
    "Café Canapé: 5.0/5 rating, gezellig café met biljart in de ruimte.",
    "Jones & Co: cosy bar in het hart van Antwerpen, beschreven als 'best drink experience'.",
    "An Sibhin: drukke Irish Pub met goed beoordelingen.",
    "Cafe Quinten Matsijs: 4.3/5, klassieke keuze in de buurt.",
    "The Northerner: 4.8/5 rating, moderne optie voor bierliefhebbers.",
    "'t Kafee: traditioneel café met ruim 100+ reviews op TripAdvisor.",
]

FOOD_TIPS = [
    "Frituur n°1 van Antwerpen — iedere Antwerpenaar heeft zijn eigen mening",
    "De Barak aan de Linkeroever heeft de beste frites volgens velen.",
    "Fish a'gogo: visgerechten met een ziel, vlak bij de kaaien.",
    "Exki is toeristenvoer. Ga voor een echt frituur.",
    "Balls & Glory op de Kloosterstraat: gehaktballen als kunstvorm.",
    "Het Antwerpse handje verwijst naar de hand van Silvius Brabo. Eén mythe, oneindig bakvormen.",
    "Het bolleke-glas van De Koninck (1833) kent geen. Herkenbaar op elk terras in de stad.",
    "Elixir d'Anvers (1863): ooit medicijn, nu likeur. Werking nooit bewezen, verkoop nooit stilgevallen.",
    "Mosselen komen uit Zeeland, friet uit de Westhoek. België claimt de combinatie — en terecht.",
    "Brabo hakte de hand van een tolgaarder af. Antwerpen tegen riviertollen: een familietraditie.",
    "Heel chique: Zilte is het enige 3-sterren Michelin restaurant van de stad",
]

QUOTES_MORNING = [
    "Goedemorgen. Nog even doorbijten, het bier wacht.",
    "Vandaag is het transatlantische nieuws waarschijnlijk weer debiel, maar wij gaan naar Antwerpen!",
    "Sommige dingen veranderen nooit. Gelukkig het bier ook niet.",
    "Vandaag is ook weer een dag dichter bij iets dat de moeite waard is.",
    "Wie heeft er al gecheckt of Pim nog leeft? Categorietje onderweg.",
    "Is Machiel al hardlopend vertrokken? Wie checkt zijn tussentijden?",
    "Erik: check je even je navigatie ;-)",
    "JP: we zitten vlakbij water. Ik houd je handje wel vast ;-)",
    "Goedemorgen! Zijn de eitjes al gebakken, Anton?",
]

QUOTES_EVENING = [
    "In Antwerpen borrelen we lokaal. Geen BOB nodig.",
    "Nog even volhouden, Antwerpen komt in zicht!",
    "Allemaal Antwerpenaar!! Let's go!",
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

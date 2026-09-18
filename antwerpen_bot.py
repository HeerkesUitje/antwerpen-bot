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
TRIP_DATE = date(2026, 11, 27)
LAT, LON = 51.2194, 4.4025
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID", None)
RSS_URL = "https://www.vrt.be/vrtnws/nl.rss.articles.xml"

EVENING_HOUR = 16

# Debug: check of CHAT_ID en BOT_TOKEN beschikbaar zijn
print(f"[DEBUG] CHAT_ID aanwezig: {'ja' if CHAT_ID else 'NEE'}")
print(f"[DEBUG] BOT_TOKEN aanwezig: {'ja' if BOT_TOKEN else 'NEE'}")

HISTORY_FLASHBACKS = [
    "± 900-1000: de eerste vermeldingen van 'Andverpia' betreffen een nederzetting aan de Schelde. Een paar eeuwen later was het de rijkste stad van Noord-Europa. Kantooruren maken verschil.",
    "1291: Antwerpen ontvangt stadsrechten. Het archief is bewaard gebleven — beter dan menige jaarploeg van de Antwerpse brandweer later presteerde.",
    "1314: Antwerpen treedt toe tot de Hanze — zij het met enige reserves. De stad was altijd meer koopman dan teamspeler.",
    "1374: de Scheldetollen worden de belangrijkste machtsfactor in de regio. Klagen over tol is in Antwerpen dus al sinds zeven eeuwen een volwassen traditie.",
    "1488: Maximiliaan van Oostenrijk wordt na een beleg door de Antwerpenaren gedwongen akkoorden te tekenen, die hij nadien negeerde. Afgedwongen contracten: niet uitgevonden door de moderne Corporate America.",
    "1500: Antwerpen heeft ongeveer 50.000 inwoners en is de snelst groeiende handelsstad van Europa. Het tekort aan arbeidskrachten loste men toen nog op zonder conferenties.",
    "1504: het Portugese peperruim komt op de Scheldeloodsen. De specerijenhandel vestigt zich definitief in Antwerpen; Venetië kijkt jaloers toe.",
    "± 1510-1520: Quinten Massijs schildert in Antwerpen zijn geldwisselaarsparen. Het begin van een schildersgeslachtstad waar later Rubens, Van Dyck en Jordaens de kroon op drukken.",
    "1520: Dürer bezoekt Antwerpen en noteert in zijn dagboek de overvloed, de rijkdom en de overdaad. Ook toen al een stagiair-verslag van een conferentiestad.",
    "1531: de Nieuwe Beurs opent — ontworpen als een tempel, met binnenhof. Hier ontstaan vroege vormen van handel in termijncontracten en derivaten. Antwerpen schreef in de praktische zin de handleiding voor de moderne financiële markt.",
    "1543: Andreas Vesalius, geboren in Brussel maar opgeleid in Leuven, publiceert zijn anatomisch meesterwerk; de Zuidelijke Nederlanden domineren de wetenschap. Antwerpen drukt en verspreidt de kennis — zoals de stad haar eigen rol zag.",
    "1555: Christoffel Plantijn richt zijn drukkerszaak op. Binnen twintig jaar is het de grootste uitgeverij van Europa.",
    "1560: Antwerpen telt naar schatting 100.000 inwoners en is de derde stad van Europa, na Parijs en Napels. Brussel en Amsterdam zijn in vergelijking nog marginale voorzieningen.",
    "1563: het Stadhuis op de Grote Markt komt gereed. Renaissance-architectuur met een boodschap: wij zijn hier de macht, niet uw landvoogd.",
    "1566: de Beeldenstorm raast op 20 augustus door Antwerpen. Kerken worden leeggehaald; de economie kantelt onmiddellijk mee. Interieur slopen bleek ook in de zestiende eeuw slecht voor het rendement.",
    "1567: de hertog van Alva arriveert met zijn troepen en de Raad van Beroerten. De zakenlui vertrekken massaal noordwaarts. De Amsterdamse vastgoedmarkt start hier formeel haar carrière.",
    "4 november 1576: de Spaanse Furie. muitende soldaten plunderen Antwerpen dagenlang, met honderden tot duizenden doden. De stad brandt en herstelt zich gedurende decennia — doch niet volledig.",
    "1576: na de Furie wordt de Pacificatie van Gent gesloten. Overleg als noodrem: het houdt de vrede drie jaar vast.",
    "17 augustus 1585: na dertien maanden beleg geeft Antwerpen zich over aan Alexander Farnese. Zeker de helft van de bevolking vertrekt noordwaarts. Geschiedkundigen beschouwen dit het startsein voor de Gouden Eeuw van Amsterdam. Antwerpen heeft er nooit een excuusbrief over ontvangen.",
    "1585-1795: de Schelde is vanaf de val van de stad gesloten voor zeevaart. Twee eeuwen stagnatie in één miliair besluit. Het is de meest import-export onevenwichtige beslissing uit de Europese geschiedenis.",
    "1599: Anthony van Dyck wordt in Antwerpen geboren. Op zijn twintigste is hij assistent van Rubens, op zijn eenentwintig meester zelf. Carrièresnelheid avant la lettre.",
    "1610-1620: Rubens runt zijn atelier aan de Wapper met tientallen medewerkers, correspondert met vorstenhuizen en onderhandelt als diplomaat. De werkgever van de zeventiende eeuw.",
    "1637: Blaeu publiceert zijn kaart van Antwerpen in de grote stedenboeken van de Republiek. Antwerpen als noodgedwongen studie-object van de concurrerende republiek.",
    "1663: de Antwerpse Sint-Lucasgilde erkent ondertussen alleen het leerlingstelsel. Het corporatisme bestaat in de stad sinds zes eeuwen en overleeft alles — inclusief twee valperioden.",
    "1706: tijdens de Spaanse Successieoorlog trekken geallieerde troepen de stad binnen. Antwerpen wisselt de komende halve eeuw vier keer van soeverein. De administratie oefende destijds in agile werken.",
    "1746-1748: Fransen bezetten Antwerpen, vertrekken, en keren in 1794 definitief terug. De stad krijgt in die periode het revolutionaire Elan cadeau, inclusief inventarisatie van kerkbezit. Veel daarvan is daarna ergens anders terechtgekomen.",
    "1796: onder Frans bewind wordt de Schelde heropend. Napoleon noemt Antwerpen 'een pistool gericht op het hart van Engeland'. Compliment, maar uitgesproken met militaire frequentie.",
    "1803-1813: Napoleon laat dokken en scheepswerven bouwen voor een invasievloot tegen Engeland. De haveninfrastructuur werd gebouwd, de invasie vond nooit plaats. Filed under: infrastructurele successen met strategische reserves.",
    "1815-1830: onder het Verenigd Koninkrijk der Nederlanden wordt Antwerpen opnieuw een factor van formaat. Willem I investeert zwaar in de haven — een waarborg die in 1830 strategisch ongunstig uitpakte voor Den Haag.",
    "27 oktober 1830: de citadel van Antwerpen wordt door de Nederlanders ingenomen. Twee jaar blijft de stad in oorlogsstaat, tot het garnizoen zich in 1832 overgeeft aan het Franse leger. Onafhankelijkheid bleek een project met nasleep.",
    "1839: het Verdrag van Londen erkent België, en bevestigt tegelijk de vrijheid van de Schelde. Juridisch een vredesverdrag; commercieel een herstartmotor.",
    "1863: Nederland en België schaften eindelijk de Scheldetollen af. Antwerpen viert dit als nationale bevrijding — terecht, want hierna begint de moderne haven grootschalig te groeien.",
    "1885: de haven van Antwerpen passeert Rotterdam in tonnage voor het eerst in twee eeuwen. Teruggenomen omzet: de Rijnlandse economie herneemt haar historische logica.",
]

FACTS = [
    "De Onze-Lieve-Vrouwetoren werd begonnen in 1352 en pas in 1521 als 'klaar' beschouwd. Ruim anderhalve eeuw bouwen: ook klantenbinding, maar dan uit de middeleeuwen.",
    "De kathedraal had twee torens moeten krijgen. De tweede kwam er nooit; het geld was op en het enthousiasme ook.",
    "In de kathedraal hangt Rubens' 'De Kruisafneming'. Wie met de trein komt, kan hem niet missen. Wie de moeite neemt, vergeet hem niet.",
    "In de Onze-Lieve-Vrouwekerk staat een madonna van Michelangelo. Doorgegaan voor Italiaanse zakenmensen en Antwerpse kooplieden, zoals dat toen ging.",
    "Michelangelo's madonna werd door Antwerpse kooplieden voor hun parochiekerk gekocht. Ze wilden katholieke kerk sieren, geen depot. Respect.",
    "Rond 1560 was Antwerpen de rijkste stad ten noorden van de Alpen, met ruim 100.000 inwoners. Amsterdam was toen nog het equivalent van een dorp met ambitionele mentaliteit.",
    "Antwerpen was in de zestiende eeuw het commerciële hart van Europa: graan uit de Oostzee, zilver uit Spanje, specerijen uit Lissabon. Alles passeerde de Schelde.",
    "In 1568 barstte de Beeldenstorm precies in Antwerpen los. Reactie van de macht: niet fraai. Zeventig jaar godsdiensttwist het gevolg.",
    "In 1585 viel Antwerpen in Spaanse handen en sloot Alexander Farnese de Schelde. De bloei was abrupt voorbij. Amsterdam heeft het nooit expliciet bedankt — financieel echter indirect ruim, want de Antwerpse handelssamenleving vertrok noordwaarts.",
    "Tot 1863 betaalden schepen op weg naar Antwerpen tol aan Nederland. Twee eeuwen lang heette het waarborg: de Schelde moest vrij. Het werd uiteindelijk een nationaal-Belgisch incident dat decennia aansleepte.",
    "Antwerpenaars staan erom bekend dat ze historische wrok koesteren over de blokkade van 1585. Redelijk, gezien het geheel.",
    "De diamantsector vestigde zich in de vijftiende eeuw in Antwerpen, mede doordat Bruges het contact verloor met de Levant. Goede havens huilen niet, die verhuizen.",
    "Rond het Centraal Station zit het diamantkwartier: in enkele straten wordt naar schatting vier vijfde van de wereldvoorraad ruwe diamanten verhandeld.",
    "De haven van Antwerpen is de op één na grootste haven van Europa en behoort tot de top twintig wereldwijd. Ruim 250 miljoen ton lading per jaar.",
    "De Kieldrecht-sluis is de grootste sluis ter wereld: 500 meter lang, 68 meter breed. Er kan een volledig fregat in, met ruimte voor het onderhoudspersoneel.",
    "Rond de haven ligt het op één na grootste petrochemische cluster ter wereld, na Houston. Uw benzine en uw douchebenodigdheden komen dus mogelijk uit Antwerpen.",
    "Centraal Station opende in 1905 en wordt de 'spoorwegkathedraal' genoemd: 75 meter koepelhoogte, vier architecten, en ondertussen een stationsgebouw dat het centrale punt van de stad vormt.",
    "De 'Antwerp Six' — onder wie Dries Van Noten en Ann Demeulemeester — reden in 1986 in een gehuurde bus naar Londen en zetten de internationale modevoeding op zijn kop. Zonder geld, zonder uitnodiging.",
    "De modeacademie van Antwerpen geldt als een van de invloedrijkste modescholen ter wereld. Toelating is selectief, output wereldwijd gerespecteerd.",
    "De ZOO van Antwerpen bestaat sinds 1843 en is een van de oudste dierentuinen van Europa. Pal naast het station, zodat zelfs een treinstaking je bezoek niet onmogelijk maakt.",
    "In 1920 organiseerde Antwerpen de Olympische Spelen — na een wereldoorlog, op het stadion waar nu weinig meer van herinnert. Historici zijn het erover eens: het houdt de Spelen van Parijs 1924 in de hand gewerkt.",
    "Op de Spelen van Antwerpen in 1920 werd voor het eerst de vlag met vijf ringen gebruikt en de olympische eed uitgesproken. Antwerpen heeft dit nooit expliciet als verdienste geclaimd — onverstandig.",
    "Via de Red Star Line vertrokken ruim twee miljoen Europeanen vanuit Antwerpen naar Noord-Amerika. Onder hen Albert Einstein. Iedereen die familie in de VS heeft, kan de reis langs Antwerpen getraceerd.",
    "Het Plantin-Moretus Museum bewaart de oudste nog werkzame drukpersen van de wereld, en was in de zestiende eeuw een van de grootste uitgeverijen van Europa.",
    "In 1568-1573 drukte Plantijn in Antwerpen de veeltalige 'Antwerpse Polyglotbijbel'. Wetenschappelijk toptijdperk — een boek van Europa-overtreffende inzet.",
    "Hendrik Conscience schreef in Antwerpen 'De Leeuw van Vlaanderen' (1838), het boek dat het Vlaamse zelfbewustzijn aanzienlijk voedde. Het stadsbeeld herdenkt hem op passende wijze.",
    "De Sint-Annatunnel onder de Schelde dateert uit 1933 en heeft de originele houten roltrappen nog. Vermoedelijk functioning as designed; iets zachter, iets langzamer, wel degelijk 1933.",
    "De Vlaeykensgang bestaat sinds 1591 en overleefde alle stadsvernieuwing. Bij zelfvertrouwen van stedenbouwkundigen: ga er even heen.",
    "Het Steen is het oudste gebouw van Antwerpen, daterend uit de dertiende eeuw. Het diende als middeleeuws burchtkasteel, gevangenis en museum. Momenteel vormt het een bezoekerscentrum voor de reizigers die de stad niet kennen.",
    "De mythische reus Antigoon eiste tol van schippers op de Schelde. De Romeinse held Silvius Brabo hakte de hand eraf en wierp die in de rivier. Economische dragers zijn er nooit van overtuigd.",
    "De echte naamverklaring van Antwerpen is echter archeologisch minder theatraal: 'aandewerpen', het land dat tegen de stroom in opgeworpen wordt. Wetenschap versus folklore: beide populair in de stad.",
    "Het MAS is 62 meter hoog, telt tien verdiepingen en werd in 2011 geopend. Moderne architectuur in een stad die historische neveneren niet schuwt.",
    "Op de Groenplaats staat het standbeeld van Rubens, in 1843 onthuld. Rubens zelf was toen reeds 200 jaar overleden — snoeitraag, maar de begroeting is permanent.",
    "De Meir is een van de drukste winkelstraten van België. Het Koninklijk Paleis erlangs diende Napoleon, Willem I en Leopold II. Nu herbergt het een winkel: evolutie heet dat.",
    "Napoleon liet in Antwerpen dokken en pakhuizen bouwen voor zijn geplande invasie van Engeland. De scheepswerven bestaan nog; de invasie is nooit gekomen.",
    "De Koninck wordt sinds 1833 in Antwerpen gebrouwen. Het bolvormige glas werd internationaal zo iconisch dat men het 'bolleke' noemt.",
    "Elixir d'Anvers wordt sinds 1863 gestookt op basis van kruiden en citrusvruchten. Medicinaal nut is niet aangetoond; artistieke claims des te meer.",
    "Het Sportpaleis behoort tot de grootste indoorarena's van Europa en wordt wereldwijd als podiumpartner voor artiesten gerespecteerd.",
    "Antwerpen telt inwoners uit meer dan 170 nationaliteiten. Superdiversiteit als sociaal-demografische realiteit — niet als campagne-slogan.",
    "De stad heeft ruim 530.000 inwoners, het grootste stedelijke gebied van België inclusief Antwerpen-Noord? De agglomeratie steekt boven de miljoen.",
    "Antwerpen meet 204 vierkante kilometer — inclusief haveninfrastructuur die zelf een stad kan herbergen.",
    "Antwerpenaren heten 'Sinjoren', een verbastering van het Spaanse 'señores'. Volgens de Nederlanders is dat al te gek; volgens de Sinjoren zelf is het verdiend.",
    "Het symbool van de stad is de hand — terug te vinden in sokkels, koekjes en sermoenen. Eén hand geworpen, eeuwenlang hergebruikt.",
    "In het Nationaal Scheepvaartmuseum (in het Steen-omgeving geopend) wordt de havenhistorie uitgestald, van houten koggeschip tot containerschip.",
    "Fort Lillo is een dorp binnen de haven, met een handjevol inwoners, omringd door kaden en industrie. Een uithoek die de stad terloops omarmt.",
    "Doel, in het havengebied, werd grotendeels onbewoonbaar verklaard voor havenuitbreiding en is nu een 'ghost town' vol streetart. Politiek zou de schuldvraag noemenswaardig zijn.",
    "Het Middelheim is een openluchtmuseum voor beeldhouwkunst, sinds 1950 gehuisvest in een voormalig park van adel. Kunst, lucht en muurpapier in één entree.",
    "De Stadsfeestzaal op de Meir diende ooit als balzaal en werd na een brand grondig gerestaureerd tot winkelpassage. Zeventig jaar balzaal, nu outlet-gevoel: stadse geschiedenis in een advertentie.",
    "Rubens ontwierp zijn eigen huis aan de Wapper, werkte er, entertainde er Europese elite en schuwde het pragmatisme niet. Tegenwoordig is het museumbezoek een sociologisch fenomeen.",
    "Antwerpen ligt in de 'Blue Banana', de stedelijke corridor van Londen tot Milaan. Dat klinkt als een grap; het is een serieus economisch-geografisch concept.",
]

# Wekelijkse thema's, automatisch gekozen op basis van de countdown
THEMES = {
    4: ("🏛️ GESCHIEDENIS WEEK", "Van Rubens tot de legende van Silvius Brabo."),
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
    "De Barak aan de Linkeroever heeft de beste frites!",
    "Fish a'gogo: visgerechten met een ziel, vlak bij de kaaien.",
    "Exki is toeristenvoer. Skip. Ga voor een echt frituur.",
    "Balls & Glory op de Kloosterstraat: gehaktballen als kunstvorm.",
    "Het Antwerpse handje verwijst naar de hand van Silvius Brabo. Eén mythe, oneindig bakvormen.",
    "Het bolleke-glas van De Koninck (1833) kent geen. Herkenbaar op elk terras in de stad.",
    "Elixir d'Anvers (1863): ooit medicijn, nu likeur. Werking nooit bewezen, verkoop nooit stilgevallen.",
    "Mosselen komen uit Zeeland, friet uit de Westhoek. België claimt de combinatie — en terecht.",
    "Brabo hakte de hand van een tolgaarder af. Antwerpen tegen riviertollen: een familietraditie.",
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
    """Haalt VRT-nieuws op: voorkeur voor Antwerpen, anders Vlaams terugval-artikel."""
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

        # Geen Antwerps nieuws vandaag: val terug op een algemeen artikel
        all_items = [
            (i.findtext("title", "").strip(), i.findtext("link", "").strip())
            for i in items
            if i.findtext("title", "").strip()
        ]
        if all_items:
            return random.choice(all_items)

    except Exception as e:
        print(f"Nieuws ophalen mislukt: {e}")
    return None


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


def pick_theme(countdown_days):
    weeks_left = max(0, -(-countdown_days // 7))   # afronden naar boven
    if countdown_days <= 0:
        return THEMES[0]
    return THEMES.get(min(weeks_left, 4))


def build_morning(weather, news, theme, countdown):
    current = weather["current"]
    daily = weather["daily"]
    if countdown > 1:
        countdown_text = f"Nog {countdown} nachtjes slapen! 🎉"
    elif countdown == 1:
        countdown_text = "MORGEN GAAT HET GEBEURDEN! 🚀"
    else:
        countdown_text = "HET IS ZOVER! 🎉🎉🎉"

    parts = [
        f"\U0001F305 OCHTENDEDITIE — ANTWERPEN UPDATE",
        f"{'=' * 21}",
        f"",
        countdown_text,
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
    
    if countdown > 1:
        countdown_text = f"Nog {countdown} nachtjes slapen! 🎉"
    elif countdown == 1:
        countdown_text = "MORGEN GAAT HET GEBEURDEN! 🚀"
    else:
        countdown_text = "HET IS ZOVER! 🎉🎉🎉"

    parts = [
        f"\U0001F319 AVONDEDITIE — ANTWERPEN UPDATE",
        f"{'=' * 21}",
        f"",
        countdown_text,
        "",
        f"{theme[0]}: {theme[1]}",
        f"",
        f"\U0001F37A TIP VAN DE AVOND",
        f"{tip}",
        "",
        f"\U0001F4A1 FEITJE VAN DE DAG",
        f"{random.choice(FACTS)}",
        "",
        f"\U0001F4DC GESCHIEDENIS HERHAALT ZICH",
        f"{random.choice(HISTORY_FLASHBACKS)}",
        "",
        f"\U0001F44B {random.choice(QUOTES_EVENING)}",
    ]
    return "\n".join(parts)

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
    now = datetime.now().hour
    if len(sys.argv) > 1:
        is_evening = sys.argv[1].strip().lower() in ("avond", "evening")
    else:
        is_evening = now >= 18
    
    countdown = (TRIP_DATE - date.today()).days
    theme = pick_theme(countdown)
    weather = get_weather()

    if is_evening:
        message = build_evening(weather, theme, countdown)
    else:
        news = get_antwerp_news()
        message = build_morning(weather, news, theme, countdown)

     # Print het bericht in de log
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

    # Foto versturen
    photos = glob.glob("*.jpg")
    if photos and chat_ids and random.random() < 0.5:
        foto = random.choice(photos)
        for cid in chat_ids:
            send_photo(foto, "📸 TERUGBLIK om bij vooruit te kijken :)", target_chat=str(cid))

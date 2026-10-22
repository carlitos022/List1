#!/usr/bin/env python3
"""Catálogo editorial: solo señales dedicadas a UNA serie o franquicia.

No se infiere que un canal infantil/series genérico sea monoserie. Los títulos
son candidatos reconocibles por nombre/ID y requieren una prueba HLS positiva
para la variante '-verificados'. No certifica emisión ininterrumpida.
"""
from __future__ import annotations

import re
import unicodedata

# Título para la guía, clase e identificadores de canales temáticos.
# Pueden existir títulos sin enlace disponible; se incorporan automáticamente
# solo cuando una fuente verificada en el workflow publica un canal específico.
CATALOGO = {
    "Bob Esponja": ("Infancia", (
        "BobEsponja", "BobEsponjaPantalonesCuadrados", "SpongeBobSquarePants",
        "SuperSpongebob", "SuperSpongeBob",
    )),
    "Ben 10": ("Infancia", ("Ben10", "Ben10AlienForce", "Ben10FuerzaAlienigena",
                            "Ben10UltimateAlien", "Ben10Omniverse")),
    "Avatar: La Leyenda de Aang": ("Infancia", (
        "AvatarLaLeyendadeAang", "AvatarTheLastAirbender", "Avatar",
    )),
    "Rugrats": ("Infancia", ("Rugrats", "SuperRugrats")),
    "Hey Arnold!": ("Infancia", ("HeyArnold", "OyeArnold")),
    "Jimmy Neutron": ("Infancia", ("JimmyNeutron", "TheAdventuresofJimmyNeutron")),
    "iCarly": ("Infancia", ("iCarly", "SuperIcarly")),
    "Kenan & Kel": ("Infancia", ("KenanKel", "KenanAndKel")),
    "Danny Phantom": ("Infancia", ("DannyPhantom",)),
    "Los padrinos mágicos": ("Infancia", ("TheFairlyOddParents", "LosPadrinosMagicos", "FairlyOddParents")),
    "Pingu": ("Infancia", ("Pingu",)),
    "Teletubbies": ("Infancia", ("Teletubbies",)),
    "Peppa Pig": ("Infancia", ("PeppaPig", "PeppaPigTV")),
    "Pocoyó": ("Infancia", ("Pocoyo",)),
    "Garfield y sus amigos": ("Infancia", ("GarfieldAndFriends", "Garfieldysusamigos", "GarfieldandFriends")),
    "Coraje el perro cobarde": ("Infancia", ("CorajeElPerroCobarde", "CourageTheCowardlyDog")),
    "El laboratorio de Dexter": ("Infancia", ("DextersLaboratory", "ElLaboratoriodeDexter")),
    "Tom y Jerry": ("Infancia", ("TomAndJerry", "TomyJerry")),
    "Scooby-Doo": ("Infancia", ("ScoobyDoo",)),
    "Los Picapiedra": ("Infancia", ("TheFlintstones", "LosPicapiedra")),
    "Los Supersónicos": ("Infancia", ("TheJetsons", "LosSupersonicos")),
    "Las Tortugas Ninja": ("Infancia", ("TeenageMutantNinjaTurtles", "LasTortugasNinja")),
    "Los Pitufos": ("Infancia", ("TheSmurfs", "LosPitufos", "OsSmurfs")),
    "El Chavo": ("Infancia", ("ElChavoTV", "ElChavo", "ElChavoAnimado")),
    "Las aventuras de Bob el Constructor": ("Infancia", ("BobTheBuilder",)),
    "Winx Club": ("Infancia", ("WinxClub",)),
    "Hora de Aventura": ("Infancia", ("AdventureTime", "HoradeAventura")),
    "La Pantera Rosa": ("Infancia", ("PinkPanther", "LaPanteraRosa")),
    "Dragon Ball Super": ("Anime", ("DragonBallSuper",)),
    "Dragon Ball Z": ("Anime", ("DragonBallZ",)),
    "Dragon Ball GT": ("Anime", ("DragonBallGT",)),
    "Dragon Ball": ("Anime", ("DragonBall",)),
    "Pokémon": ("Anime", ("Pokemon", "PlutoTVPokemon", "PokemonenEspanol")),
    "Digimon": ("Anime", ("Digimon", "DigimonAdventure")),
    "Sailor Moon": ("Anime", ("SailorMoon",)),
    "Naruto": ("Anime", ("Naruto", "NarutoShippuden")),
    "One Piece": ("Anime", ("OnePiece",)),
    "Detective Conan": ("Anime", ("DetectiveConan",)),
    "Los Caballeros del Zodiaco": ("Anime", ("SaintSeiya", "CaballerosdelZodiaco")),
    "Death Note": ("Anime", ("DeathNote",)),
    "Futurama": ("Animación adulta", ("Futurama",)),
    "Los Simpson": ("Animación adulta", ("TheSimpsons", "LosSimpson", "LosSimpsons")),
    "South Park": ("Animación adulta", ("SouthPark",)),
    "Padre de familia": ("Animación adulta", ("FamilyGuy", "PadredeFamilia")),
    "Los Vengadores": ("Superhéroes", ("Avengers", "TheAvengers", "LosVengadores")),
    "Batman: La serie animada": ("Superhéroes", ("BatmanTheAnimatedSeries", "BatmanLaSerieAnimada")),
    "Smallville": ("Series", ("Smallville",)),
    "The Walking Dead": ("Series", ("TheWalkingDead", "TheWalkingDeadenEspanol", "TheWalkingDeadbyAMC")),
    "Breaking Bad": ("Series", ("BreakingBad",)),
    "Dr. House": ("Series", ("HouseMD", "DrHouse", "House")),
    "Supernatural": ("Series", ("Supernatural",)),
    "Malcolm": ("Series", ("MalcolmInTheMiddle", "Malcolm")),
    "Alf": ("Series", ("ALF",)),
    "El Príncipe del Rap": ("Series", ("TheFreshPrinceofBelAir", "ElPrincipedelRap")),
    "CSI: Miami": ("Series", ("CSIMiami",)),
    "NCIS": ("Series", ("NCIS",)),
    "Medium": ("Series", ("Medium",)),
    "3Cat Plats Bruts": ("Series", ("3CatPlatsbruts",)),
    "El Comisario": ("Series", ("ElComisario",)),
    "Curro Jiménez": ("Series", ("CurroJimenez",)),
    "Los asesinatos de Midsomer": ("Series", ("LosAsesinatosdeMidsomer",)),
    "Star Trek: Voyager": ("Series", ("StarTrekVoyager",)),
    "Acapulco Shore": ("Series", ("AcapulcoShore",)),
    "El encantador de perros": ("Series", ("Elencantadordeperros",)),
    "La Rosa de Guadalupe": ("Series", ("LaRosadeGuadalupe",)),
    "El secreto de Feriha": ("Novelas", ("ElsecretodeFeriha",)),
    "¿Qué culpa tiene Fatmagül?": ("Novelas", ("QueCulpaTieneFatmagul",)),
    "Rebelde": ("Novelas", ("Rebelde",)),
    "Ana y los 7": ("Series", ("Anaylos7",)),
}

def slug(valor: str) -> str:
    plain = unicodedata.normalize("NFKD", valor)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", plain.lower())


INDEX = {
    slug(alias): (title, kind)
    for title, (kind, aliases) in CATALOGO.items()
    for alias in aliases
}


def identificar(entry: dict) -> tuple[str, str] | None:
    """Busca por identificación EXACTA para evitar canales de contenido mixto."""
    id_ = entry.get("tvg_id", "").split(".", 1)[0].strip()
    if id_:
        hit = INDEX.get(slug(id_))
        if hit:
            return hit
        # No aceptar el nombre como respaldo si la ID identificó otro canal.
        return None
    name = entry.get("name", "").strip()
    name = re.sub(r"\s*[\(\[](?:\d{3,4}p|HD|SD|FHD|4K|LatAm|US|Spain|Germany)[\)\]]", "", name, flags=re.I)
    name = re.sub(r"\s+24\s*/\s*7$", "", name)
    name = re.sub(r"\s*\[(?:Geo-blocked|Not 24/7)\]$", "", name, flags=re.I)
    return INDEX.get(slug(name))


def seleccionar(entradas: list[dict]) -> list[dict]:
    """Un solo canal por ID+URL; excluye televisión de géneros mezclados."""
    encontrados: dict[tuple[str, str], dict] = {}
    for entry in entradas:
        if "[Not 24/7]" in entry.get("name", ""):
            continue
        identificacion = identificar(entry)
        if not identificacion:
            continue
        titulo, categoria = identificacion
        key = (titulo, entry.get("url", ""))
        if not key[1] or key in encontrados:
            continue
        copia = dict(entry)
        copia["titulo_247"] = titulo
        copia["grupo_247"] = f"📺 24/7 • {categoria}"
        # El título es editorial, la disponibilidad se audita aparte.
        encontrados[key] = copia
    return sorted(encontrados.values(), key=lambda e: (
        e["grupo_247"], e["titulo_247"].casefold(), e["name"].casefold()
    ))

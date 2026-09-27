#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import urllib.request
from pathlib import Path
from collections import Counter

SOURCE = "https://iptv-org.github.io/iptv/languages/spa.m3u"
OUTDIR = Path(__file__).resolve().parent
ROOT = OUTDIR.parent
USER_AGENT = "Mozilla/5.0 IPTV-Espanol-Classifier/1.0"

COUNTRY_LABELS = {
    "ec": "🇪🇨 Ecuador", "es": "🇪🇸 España", "co": "🇨🇴 Colombia",
    "mx": "🇲🇽 Mexico", "ar": "🇦🇷 Argentina", "pe": "🇵🇪 Peru",
    "cl": "🇨🇱 Chile", "ve": "🇻🇪 Venezuela", "bo": "🇧🇴 Bolivia",
    "py": "🇵🇾 Paraguay", "uy": "🇺🇾 Uruguay", "cr": "🇨🇷 Costa Rica",
    "pa": "🇵🇦 Panama", "gt": "🇬🇹 Guatemala", "hn": "🇭🇳 Honduras",
    "sv": "🇸🇻 El Salvador", "ni": "🇳🇮 Nicaragua",
    "do": "🇩🇴 Republica Dominicana", "pr": "🇵🇷 Puerto Rico", "cu": "🇨🇺 Cuba",
}
LATAM_CODES = {
    "ec","co","mx","ar","pe","cl","ve","bo","py","uy","cr","pa",
    "gt","hn","sv","ni","do","pr","cu"
}
COUNTRY_PRIORITY = ["ec","es","co","mx","ar","pe","cl","ve"]

CATEGORY_LABELS = {
    "sports": "⚽ Deportes", "sport": "⚽ Deportes",
    "movies": "🎬 Peliculas", "movie": "🎬 Peliculas",
    "series": "📺 Series", "news": "📰 Noticias", "music": "🎵 Musica",
    "kids": "👶 Infantiles", "children": "👶 Infantiles",
    "documentary": "📚 Documentales", "documentaries": "📚 Documentales",
    "religious": "⛪ Religion", "religion": "⛪ Religion",
    "general": "📺 General", "entertainment": "🎭 Entretenimiento",
    "culture": "🎨 Cultura", "family": "👨‍👩‍👧 Familiar",
    "education": "🎓 Educacion", "legislative": "🏛️ Legislativo",
    "lifestyle": "🌿 Estilo de vida", "business": "💼 Negocios",
    "weather": "🌤️ Clima", "travel": "✈️ Viajes", "cooking": "🍳 Cocina",
    "animation": "🧸 Animacion", "comedy": "😂 Comedia", "shop": "🛍️ Compras",
    "science": "🔬 Ciencia", "outdoor": "🏕️ Aire libre",
    "classic": "🎞️ Clasicos", "auto": "🚗 Motor",
}
CATEGORY_PRIORITY = [
    "⚽ Deportes", "🎬 Peliculas", "📺 Series", "📰 Noticias", "🎵 Musica",
    "👶 Infantiles", "📚 Documentales", "⛪ Religion", "📺 General",
    "🎭 Entretenimiento", "🎨 Cultura", "👨‍👩‍👧 Familiar", "🎓 Educacion"
]

SPECIAL_COUNTRIES = {
    "ec": "ECUADOR", "es": "ESPANA", "co": "COLOMBIA", "mx": "MEXICO",
    "ar": "ARGENTINA", "pe": "PERU", "cl": "CHILE", "ve": "VENEZUELA",
}
SPECIAL_COUNTRY_ORDER = [
    "ECUADOR","ESPANA","COLOMBIA","MEXICO","ARGENTINA","PERU","CHILE",
    "VENEZUELA","OTROS LATINOAMERICA"
]
SPECIAL_CATEGORY_MAP = {
    "sports": "DEPORTES", "sport": "DEPORTES",
    "movies": "PELICULAS", "movie": "PELICULAS",
    "series": "SERIES", "news": "NOTICIAS", "music": "MUSICA",
    "kids": "INFANTILES", "children": "INFANTILES",
    "documentary": "DOCUMENTALES", "documentaries": "DOCUMENTALES",
    "religious": "RELIGION", "religion": "RELIGION",
}
SPECIAL_CATEGORY_ORDER = [
    "DEPORTES","PELICULAS","SERIES","NOTICIAS","MUSICA",
    "INFANTILES","DOCUMENTALES","RELIGION"
]

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')

def download() -> str:
    req = urllib.request.Request(SOURCE, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def parse_entries(text: str):
    lines = [ln.rstrip("\r") for ln in text.splitlines()]
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("#EXTINF:"):
            i += 1
            continue
        extinf = line
        extras = []
        i += 1
        while i < len(lines) and lines[i].startswith("#") and not lines[i].startswith("#EXTINF:"):
            extras.append(lines[i])
            i += 1
        if i >= len(lines) or not lines[i] or lines[i].startswith("#"):
            continue
        url = lines[i].strip()
        attrs = dict(ATTR_RE.findall(extinf))
        tvg_id = attrs.get("tvg-id", "")
        m = re.search(r'\.([a-zA-Z]{2})@', tvg_id)
        cc = m.group(1).lower() if m else ""
        original_group = attrs.get("group-title", "General").strip() or "General"
        cat = CATEGORY_LABELS.get(original_group.lower(), f"📁 {original_group}")
        name = extinf.split(",", 1)[1].strip() if "," in extinf else tvg_id or url
        entries.append({
            "extinf": extinf, "extras": extras, "url": url, "cc": cc,
            "original_group": original_group, "category": cat, "name": name
        })
        i += 1
    return entries

def country_label(cc: str) -> str:
    if cc in COUNTRY_LABELS:
        return COUNTRY_LABELS[cc]
    if cc in LATAM_CODES:
        return "🌎 Otros Latinoamerica"
    return "🌐 Otros en espanol"

def country_sort_key(cc: str):
    if cc in COUNTRY_PRIORITY:
        return (0, COUNTRY_PRIORITY.index(cc), "")
    if cc in LATAM_CODES:
        return (1, 0, country_label(cc))
    return (2, 0, country_label(cc))

def category_sort_key(cat: str):
    try:
        return (0, CATEGORY_PRIORITY.index(cat), cat)
    except ValueError:
        return (1, 999, cat)

def replace_group(extinf: str, new_group: str) -> str:
    if 'group-title="' in extinf:
        return re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf, count=1)
    comma = extinf.find(",")
    if comma == -1:
        return extinf + f' group-title="{new_group}"'
    return extinf[:comma] + f' group-title="{new_group}"' + extinf[comma:]

def write_playlist(path: Path, entries, mode: str):
    out = ["#EXTM3U"]
    for e in entries:
        country = country_label(e["cc"])
        cat = e["category"]
        if mode == "hybrid":
            group = f"{country} • {cat}"
        elif mode == "country":
            group = country
        else:
            group = cat
        out.append(replace_group(e["extinf"], group))
        out.extend(e["extras"])
        out.append(e["url"])
    path.write_text("\n".join(out) + "\n", encoding="utf-8")

def special_country_group(cc: str):
    if cc in SPECIAL_COUNTRIES:
        return SPECIAL_COUNTRIES[cc]
    if cc in LATAM_CODES:
        return "OTROS LATINOAMERICA"
    return None

def write_special_playlist(path: Path, entries):
    locals_ = [e for e in entries if special_country_group(e["cc"])]
    locals_.sort(key=lambda e: (
        SPECIAL_COUNTRY_ORDER.index(special_country_group(e["cc"])),
        e["name"].casefold()
    ))

    thematic = []
    for e in entries:
        group = SPECIAL_CATEGORY_MAP.get(e["original_group"].lower())
        if group:
            copy = dict(e)
            copy["special_category"] = group
            thematic.append(copy)
    thematic.sort(key=lambda e: (
        SPECIAL_CATEGORY_ORDER.index(e["special_category"]),
        e["name"].casefold()
    ))

    out = ["#EXTM3U"]
    for e in locals_:
        out.append(replace_group(e["extinf"], special_country_group(e["cc"])))
        out.extend(e["extras"])
        out.append(e["url"])
    for e in thematic:
        out.append(replace_group(e["extinf"], e["special_category"]))
        out.extend(e["extras"])
        out.append(e["url"])

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(locals_), len(thematic)

def main():
    entries = parse_entries(download())

    by_country = sorted(
        entries,
        key=lambda e: (country_sort_key(e["cc"]), category_sort_key(e["category"]), e["name"].casefold())
    )
    by_category = sorted(
        entries,
        key=lambda e: (category_sort_key(e["category"]), country_sort_key(e["cc"]), e["name"].casefold())
    )

    write_playlist(OUTDIR / "espanol.m3u", by_country, "hybrid")
    write_playlist(OUTDIR / "por-pais.m3u", by_country, "country")
    write_playlist(OUTDIR / "por-categoria.m3u", by_category, "category")

    ecuador = [e for e in by_country if e["cc"] == "ec"]
    write_playlist(OUTDIR / "ecuador.m3u", ecuador, "category")

    special_path = OUTDIR / "espanol-paises-y-categorias.m3u"
    local_count, thematic_count = write_special_playlist(special_path, entries)

    # tv.m3u es siempre un espejo de la lista especial usada en Smart TV.
    shutil.copyfile(special_path, ROOT / "tv.m3u")

    stats = Counter(country_label(e["cc"]) for e in entries)
    (OUTDIR / "ESTADISTICAS.txt").write_text(
        "Fuente: " + SOURCE + "\n"
        + f"Canales procesados: {len(entries)}\n"
        + f"Entradas locales lista TV: {local_count}\n"
        + f"Entradas tematicas lista TV: {thematic_count}\n\n"
        + "\n".join(f"{k}: {v}" for k, v in stats.most_common())
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Generadas listas con {len(entries)} canales; "
        f"Ecuador: {len(ecuador)}; TV: {local_count + thematic_count} entradas"
    )

if __name__ == "__main__":
    main()

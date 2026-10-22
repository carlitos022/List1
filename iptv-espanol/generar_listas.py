#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import urllib.request
from pathlib import Path
from collections import Counter
from canales_monoserie import CATALOGO, seleccionar

SOURCE = "https://iptv-org.github.io/iptv/languages/spa.m3u"
EXTRA_CATEGORY_SOURCES = {
    "PELICULAS": "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "SERIES": "https://iptv-org.github.io/iptv/categories/series.m3u",
}
FREE_TV_SOURCE = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
SHOW_SOURCE_URLS = {
    "kids.m3u": "https://iptv-org.github.io/iptv/categories/kids.m3u",
    "animation.m3u": "https://iptv-org.github.io/iptv/categories/animation.m3u",
    "comedy.m3u": "https://iptv-org.github.io/iptv/categories/comedy.m3u",
}
EXTRA_24_7_IDS = {
    "PELICULAS": {
        "CineRomantico.us@SD",
        "PlutoTVComediasRomanticas.de@ES",
        "PlutoTVSciFi.de@ES",
        "PlutoTVSciFi.us@LatAm",
        "PlutoTVZombies.de@ES",
        "Medium.de@ES",
        "StarTrekVoyager.de@ES",
    },
    "SERIES": {
        "Medium.de@ES",
        "PlutoTVSciFi.de@ES",
        "PlutoTVSciFi.us@LatAm",
        "PlutoTVTrueCrime.de@ES",
        "PlutoTVZombies.de@ES",
        "StarTrekVoyager.de@ES",
        "TelemundoTelenovelasClasicas.us@SD",
    },
}
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

def download_url(url: str) -> str:
    # Reutilizar exactamente las fuentes verificadas por sincronizar_fuentes.py.
    source_dir = os.environ.get("IPTV_SOURCE_DIR")
    if source_dir:
        allowed = {SOURCE, FREE_TV_SOURCE, *EXTRA_CATEGORY_SOURCES.values(), *SHOW_SOURCE_URLS.values()}
        if url not in allowed:
            raise ValueError(f"Fuente IPTV no autorizada: {url}")
        return (Path(source_dir) / url.rsplit("/", 1)[-1]).read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def download() -> str:
    return download_url(SOURCE)

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
        m = re.search(r'\.([a-zA-Z]{2})(?:@|$)', tvg_id)
        country = attrs.get("tvg-country", "").split(";", 1)[0].strip().lower()
        cc = country if len(country) == 2 else (m.group(1).lower() if m else "")
        original_group = attrs.get("group-title", "General").strip() or "General"
        cat = CATEGORY_LABELS.get(original_group.lower(), f"📁 {original_group}")
        name = extinf.rsplit(",", 1)[1].strip() if "," in extinf else tvg_id or url
        entries.append({
            "extinf": extinf, "extras": extras, "url": url, "cc": cc,
            "tvg_id": tvg_id,
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

def write_special_playlist(path: Path, entries, extra_categories=None):
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
    seen_by_group = {
        group: {
            e.get("tvg_id", "")
            for e in thematic
            if e.get("special_category") == group and e.get("tvg_id")
        }
        for group in SPECIAL_CATEGORY_ORDER
    }
    seen_urls_by_group = {
        group: {
            e["url"]
            for e in thematic
            if e.get("special_category") == group
        }
        for group in SPECIAL_CATEGORY_ORDER
    }

    for e in thematic:
        out.append(replace_group(e["extinf"], e["special_category"]))
        out.extend(e["extras"])
        out.append(e["url"])

    extra_count = 0
    if extra_categories:
        for group in SPECIAL_CATEGORY_ORDER:
            extras = extra_categories.get(group, [])
            for e in extras:
                tvg_id = e.get("tvg_id", "")
                if (tvg_id and tvg_id in seen_by_group[group]) or e["url"] in seen_urls_by_group[group]:
                    continue
                out.append(replace_group(e["extinf"], group))
                out.extend(e["extras"])
                out.append(e["url"])
                if tvg_id:
                    seen_by_group[group].add(tvg_id)
                seen_urls_by_group[group].add(e["url"])
                extra_count += 1

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(locals_), len(thematic), extra_count

# Incluir solo canales regionales o con pista explícita de audio español.
SPANISH_CODES = set(LATAM_CODES) | {"es"}
SPANISH_VARIANT = re.compile(r'@(ES|SPA|LATAM|LATINO|MX)(?:$|[^A-Za-z])', re.I)
DAYLONG_PATTERN = re.compile(r'(?<!\d)(?:24\s*[/\-]?\s*7|24\s*h(?:oras?)?|non\s*stop)(?!\w)', re.I)


def is_spanish(e):
    return (
        e["cc"] in SPANISH_CODES
        or bool(SPANISH_VARIANT.search(e["tvg_id"]))
        or e["tvg_id"] in EXTRA_24_7_IDS["PELICULAS"]
        or e["tvg_id"] in EXTRA_24_7_IDS["SERIES"]
    )


def is_stream(e):
    """Para M3U de reproductores: excluir páginas web de YouTube/Twitch."""
    from urllib.parse import urlsplit
    u = urlsplit(e["url"])
    if u.scheme not in ("http", "https") or not u.netloc:
        return False
    hostname = (u.hostname or "").lower()
    if hostname in ("youtube.com", "www.youtube.com", "youtu.be",
                    "www.twitch.tv", "twitch.tv", "facebook.com", "www.facebook.com"):
        return False
    return True


def distinct(entries):
    """Dedupe within a group, retaining metadata and the first feed."""
    seen = set()
    out = []
    for e in entries:
        key = e["url"].split("#", 1)[0].strip()
        if key and key not in seen and is_stream(e) and "[Not 24/7]" not in e["name"]:
            seen.add(key)
            out.append(e)
    return out


def write_group(path, entries, name):
    lines = ["#EXTM3U"]
    for e in entries:
        lines.append(replace_group(e["extinf"], name))
        lines.extend(e["extras"])
        lines.append(e["url"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_group(path, entries, name):
    if not entries:
        return
    with path.open("a", encoding="utf-8") as f:
        for e in entries:
            f.write(replace_group(e["extinf"], name) + "\n")
            for extra in e["extras"]:
                f.write(extra + "\n")
            f.write(e["url"] + "\n")


def write_show_playlist(path: Path, entries) -> None:
    lines = ["#EXTM3U"]
    for e in entries:
        extinf = replace_group(e["extinf"], e["grupo_247"])
        title = f'{e["titulo_247"]} 24/7'
        extinf = extinf.rsplit(",", 1)[0] + "," + title
        lines.append(extinf)
        lines.extend(e["extras"])
        lines.append(e["url"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_show_playlist(path: Path, entries) -> None:
    if not entries:
        return
    with path.open("a", encoding="utf-8") as f:
        for e in entries:
            extinf = replace_group(e["extinf"], e["grupo_247"])
            f.write(extinf.rsplit(",", 1)[0] + "," + e["titulo_247"] + " 24/7\n")
            for extra in e["extras"]:
                f.write(extra + "\n")
            f.write(e["url"] + "\n")



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

    extra_categories = {}
    for group, url in EXTRA_CATEGORY_SOURCES.items():
        category_entries = parse_entries(download_url(url))
        extra_categories[group] = distinct([e for e in category_entries if is_spanish(e)])
        print(f"Categoría {group}: {len(extra_categories[group])} señales españolas elegibles")

    free_tv = distinct([e for e in parse_entries(download_url(FREE_TV_SOURCE)) if is_spanish(e)])
    # Hay que identificar el contenido real: una emisora general, aunque emita
    # las 24 horas, NO es una señal dedicada a un único programa.
    fuentes_tematicas = []
    for url in SHOW_SOURCE_URLS.values():
        fuentes_tematicas.extend(
            e for e in parse_entries(download_url(url)) if is_spanish(e)
        )
    tv_247 = seleccionar(distinct(
        entries + extra_categories["PELICULAS"] + extra_categories["SERIES"]
        + free_tv + fuentes_tematicas
    ))
    peliculas = extra_categories["PELICULAS"]
    series = extra_categories["SERIES"]
    write_show_playlist(OUTDIR / "24-7.m3u", tv_247)
    write_group(OUTDIR / "peliculas.m3u", peliculas, "🎬 PELICULAS")
    write_group(OUTDIR / "series.m3u", series, "📺 SERIES")

    publicados = {e["titulo_247"] for e in tv_247}
    pendientes = [nombre for nombre in CATALOGO if nombre not in publicados]
    (OUTDIR / "24-7-PENDIENTES.md").write_text(
        "# Series 24/7 aún sin señal identificada en fuentes públicas\n\n"
        + "Estas series NO se inventan ni se mezclan con canales de género. "
        + "Se incorporarán automáticamente si aparece una fuente monoserie compatible.\n\n"
        + "\n".join("- " + titulo for titulo in pendientes) + "\n",
        encoding="utf-8",
    )

    special_path = OUTDIR / "espanol-paises-y-categorias.m3u"
    local_count, thematic_count, extra_count = write_special_playlist(
        special_path, entries, extra_categories
    )

    # Categoría extra conservando todas las existentes.
    append_show_playlist(special_path, tv_247)
    shutil.copyfile(special_path, ROOT / "tv.m3u")

    stats = Counter(country_label(e["cc"]) for e in entries)
    (OUTDIR / "ESTADISTICAS.txt").write_text(
        "Fuente: " + SOURCE + "\n"
        + f"Canales procesados: {len(entries)}\n"
        + f"Entradas locales lista TV: {local_count}\n"
        + f"Entradas tematicas lista TV: {thematic_count}\n"
        + f"Señales temáticas adicionales: {extra_count}\n"
        + f"Películas adicionales: {len(peliculas)}\n"
        + f"Series adicionales: {len(series)}\n"
        + f"Canales monoserie 24/7 identificados: {len(tv_247)}\n"
        + f"Canales Free-TV en español: {len(free_tv)}\n\n"
        + "\n".join(f"{k}: {v}" for k, v in stats.most_common())
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Generadas listas con {len(entries)} canales; "
        f"Ecuador: {len(ecuador)}; monoserie 24/7: {len(tv_247)}; "
        f"películas: {len(peliculas)}; series: {len(series)}; "
        f"TV: {local_count + thematic_count + extra_count + len(tv_247)} entradas"
    )

if __name__ == "__main__":
    main()

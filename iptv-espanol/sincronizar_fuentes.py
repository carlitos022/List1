#!/usr/bin/env python3
"""Sincroniza playlists IPTV solo si cambiaron las fuentes originales.

Descarga y valida las fuentes antes de regenerar. Ante errores, sale sin
publicar nuevas listas: GitHub Actions mantiene el ultimo commit valido.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import generar_listas as generador

ROOT = Path(__file__).resolve().parent.parent
DIR = Path(__file__).resolve().parent
STATE_FILE = DIR / "fuentes_estado.json"
SOURCES = {
    "spa.m3u": (generador.SOURCE, 500),
    "movies.m3u": (generador.EXTRA_CATEGORY_SOURCES["PELICULAS"], 10),
    "series.m3u": (generador.EXTRA_CATEGORY_SOURCES["SERIES"], 10),
    "playlist.m3u8": (generador.FREE_TV_SOURCE, 100),
}
OUTPUTS = {
    "tv.m3u": (ROOT / "tv.m3u", 500),
    "espanol.m3u": (DIR / "espanol.m3u", 500),
    "por-pais.m3u": (DIR / "por-pais.m3u", 500),
    "por-categoria.m3u": (DIR / "por-categoria.m3u", 500),
    "ecuador.m3u": (DIR / "ecuador.m3u", 10),
    "24-7.m3u": (DIR / "24-7.m3u", 20),
    "peliculas.m3u": (DIR / "peliculas.m3u", 10),
    "series.m3u": (DIR / "series.m3u", 10),
    "espanol-paises-y-categorias.m3u": (
        DIR / "espanol-paises-y-categorias.m3u", 500
    ),
}


def validar_fuente(texto: str, nombre: str, minimo: int) -> int:
    """Rechaza respuestas HTML, vacias y listas incompletas."""
    if not texto.lstrip("\ufeff").startswith("#EXTM3U"):
        raise ValueError(f"{nombre}: la respuesta no es una lista M3U")
    entradas = generador.parse_entries(texto)
    if len(entradas) < minimo:
        raise ValueError(
            f"{nombre}: solo {len(entradas)} entradas (minimo {minimo})"
        )
    return len(entradas)


def validar_reduccion(actual: int, anterior: int) -> None:
    """Evita publicar una fuente truncada por un fallo temporal."""
    if anterior and actual < int(anterior * 0.60):
        raise ValueError(
            f"Caida anomala de canales: {anterior} -> {actual} "
            "(mas de 40%). Se mantiene la version anterior."
        )


def leer_estado() -> dict:
    if not STATE_FILE.is_file():
        return {}
    try:
        estado = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return estado if isinstance(estado, dict) else {}
    except (ValueError, OSError):
        return {}


def descargar_con_reintentos(url: str) -> str:
    for intento in range(3):
        try:
            return generador.download_url(url)
        except Exception as error:
            if intento == 2:
                raise RuntimeError(f"No se pudo descargar {url}") from error
            print(f"Reintentando {url}: {error}", flush=True)
            time.sleep(2 ** intento)
    raise AssertionError("Descarga sin resultado")


def salidas_disponibles() -> bool:
    return all(ruta.is_file() and ruta.stat().st_size > 100 for ruta, _ in OUTPUTS.values())


def validar_salidas() -> None:
    for nombre, (ruta, minimo) in OUTPUTS.items():
        texto = ruta.read_text(encoding="utf-8")
        validar_fuente(texto, nombre, minimo)


def sincronizar(forzar: bool) -> None:
    anterior = leer_estado()
    prev_spa = anterior.get("fuentes", {}).get("spa.m3u", {}).get("entradas", 0)
    nuevas = {}

    with tempfile.TemporaryDirectory(prefix="iptv-fuentes-") as tmp:
        origenes = Path(tmp)
        for nombre, (url, minimo) in SOURCES.items():
            texto = descargar_con_reintentos(url)
            cantidad = validar_fuente(texto, nombre, minimo)
            if nombre == "spa.m3u":
                validar_reduccion(cantidad, prev_spa)
            (origenes / nombre).write_text(texto, encoding="utf-8")
            nuevas[nombre] = {
                "url": url,
                "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
                "entradas": cantidad,
            }
            print(f"Fuente {nombre}: {cantidad} entradas", flush=True)

        if (
            not forzar
            and anterior.get("fuentes") == nuevas
            and salidas_disponibles()
        ):
            print("Fuentes sin cambios. Se conserva la lista publicada.", flush=True)
            return

        print("Cambios detectados o regeneracion solicitada.", flush=True)
        entorno = os.environ.copy()
        entorno["IPTV_SOURCE_DIR"] = str(origenes)
        subprocess.run(
            [sys.executable, str(DIR / "generar_listas.py")],
            check=True,
            cwd=ROOT,
            env=entorno,
        )
        subprocess.run(
            [sys.executable, str(DIR / "filtrar_muertos.py")],
            check=True,
            cwd=ROOT,
            env=entorno,
        )
        validar_salidas()
        STATE_FILE.write_text(
            json.dumps({"version": 1, "fuentes": nuevas}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print("Listas verificadas y listas para publicar.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="Regenerar incluso si las fuentes no cambiaron",
    )
    opciones = parser.parse_args()
    try:
        sincronizar(opciones.force)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"ERROR: {e}. Se conserva la ultima version publicada.", file=sys.stderr)
        sys.exit(1)

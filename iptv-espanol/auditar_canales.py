#!/usr/bin/env python3
"""Auditor de streams HTTP/HLS. No confunde geobloqueos con enlaces rotos.

Prueba el manifiesto HLS y, cuando es posible, un segmento real de video.
Solo se excluyen enlaces tras dos auditorías separadas con fallo concluyente.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import urllib.error
import urllib.parse
import urllib.request

from generar_listas import parse_entries

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent
STATE = DIR / "salud_canales.json"
REPORT = DIR / "REPORTE_SALUD.md"
PLAYLISTS = [ROOT / "tv.m3u", DIR / "24-7.m3u",
             DIR / "peliculas.m3u", DIR / "series.m3u"]
VERIFIED_PLAYLISTS = {
    ROOT / "tv.m3u": ROOT / "tv-verificada.m3u",
    DIR / "24-7.m3u": DIR / "24-7-verificados.m3u",
    DIR / "peliculas.m3u": DIR / "peliculas-verificadas.m3u",
    DIR / "series.m3u": DIR / "series-verificadas.m3u",
}

AGENT = "Mozilla/5.0 IPTV-PublicHealthChecker/1.0"
MAX_READ = 16384


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def public_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        hostname = parsed.hostname
        if hostname.lower() in {"localhost", "localhost.localdomain"}:
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_global
        except ValueError:
            return True
    except ValueError:
        return False


class PublicOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not public_url(newurl):
            raise ValueError("Redirección a destino no público")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(PublicOnlyRedirect())


def get_sample(url: str, timeout: float) -> tuple[int, str, bytes, str]:
    """GET parcial, sin descargar el stream completo."""
    if not public_url(url):
        raise ValueError("URL no pública")
    request = urllib.request.Request(url, headers={
        "User-Agent": AGENT,
        "Accept": "*/*",
        "Range": f"bytes=0-{MAX_READ - 1}",
    })
    with OPENER.open(request, timeout=timeout) as response:
        status = response.status
        ctype = response.headers.get("content-type", "").lower()
        actual_url = response.geturl()
        if not public_url(actual_url):
            raise ValueError("Redirección a URL no pública")
        return status, ctype, response.read(MAX_READ), actual_url


def first_media_reference(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF:"):
            for nxt in lines[index + 1:]:
                if not nxt.startswith("#"):
                    return nxt
        if line.startswith("#EXT-X-MAP:"):
            import re
            match = re.search(r'URI="([^"]+)"', line)
            if match:
                return match.group(1)
        if line.startswith("#EXTINF:"):
            for nxt in lines[index + 1:]:
                if not nxt.startswith("#"):
                    return nxt
    return None


def check_stream(url: str, timeout: float = 5) -> tuple[str, str]:
    """up = bytes de media verificados; down = fallo claro; unknown = indeterminado."""
    if not public_url(url):
        return "unknown", "URL privada, local o inválida"
    try:
        status, ctype, data, actual = get_sample(url, timeout)
        if status not in (200, 206):
            return "unknown", f"HTTP {status}"
        if not data:
            return "down", "Respuesta vacía"
        head = data[:256].lstrip().lower()
        if head.startswith((b"<!doctype html", b"<html")) or "text/html" in ctype:
            return "down", "Página HTML en lugar de stream"
        body = data.decode("utf-8", errors="replace")
        if body.lstrip("\ufeff").startswith("#EXTM3U"):
            if "#EXT-X-" not in body:
                return "unknown", "M3U sin manifiesto HLS"
            reference = first_media_reference(body)
            if not reference:
                return "unknown", "Manifiesto HLS sin variantes/segmentos"
            next_url = urllib.parse.urljoin(actual, reference)
            if not public_url(next_url):
                return "unknown", "Referencia a red privada"
            status2, ctype2, sample2, actual2 = get_sample(next_url, timeout)
            if status2 not in (200, 206) or not sample2:
                return "unknown", f"Sin datos del manifiesto/segmento ({status2})"
            if sample2.lstrip().startswith(b"#EXTM3U"):
                media_ref = first_media_reference(sample2.decode("utf-8", "replace"))
                if not media_ref:
                    return "unknown", "Playlist anidada sin segmento"
                segment_url = urllib.parse.urljoin(actual2, media_ref)
                _, ctype3, bytes3, _ = get_sample(segment_url, timeout)
                if bytes3 and "text/html" not in ctype3 and not bytes3.lstrip().startswith(b"<html"):
                    return "up", "Manifiesto y segmento accesibles"
                return "unknown", "Segmento vacío/no reproducible"
            if "text/html" in ctype2 or sample2.lstrip().lower().startswith(b"<html"):
                return "unknown", "Variante devuelve HTML"
            return "up", "Manifiesto y segmento accesibles"
        if "video/" in ctype or "audio/" in ctype:
            return "up", "Stream multimedia responde"
        if data[:1] == b"\x47" or data[:4] in (b"ftyp", b"\x1a\x45\xdf\xa3"):
            return "up", "Datos multimedia"
        if ".mpd" in urllib.parse.urlsplit(actual).path.lower() and "<MPD" in body:
            return "up", "Manifiesto DASH accesible (segmentos no auditados)"
        return "unknown", "Formato de stream no reconocido"
    except urllib.error.HTTPError as error:
        if error.code in (404, 410):
            return "down", f"HTTP {error.code}"
        return "unknown", f"HTTP {error.code} (posible bloqueo o fallo temporal)"
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, ValueError) as error:
        return "unknown", f"Sin respuesta concluyente: {type(error).__name__}"


def load_state() -> dict:
    if not STATE.exists():
        return {}
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def update_record(old: dict, status: str, detail: str, day: str) -> dict:
    previous_date = old.get("date")
    count = old.get("consecutive_down", 0)
    if status == "up":
        count = 0
    elif status == "down" and previous_date != day:
        count += 1
    elif status == "unknown":
        # Nunca empeorar un estado por geobloqueo / timeout.
        pass
    record = {
        "state": status, "date": day,
        "consecutive_down": count,
        "reason": detail[:120],
    }
    if status == "unknown" and count >= 2:
        # Persisten evidencias anteriores, no se elimina un veto confirmado
        # por una comprobación indeterminada.
        record["state"] = "down_confirmed_previous"
    return record


def load_urls() -> tuple[list[str], dict[str, set[str]]]:
    urls = set()
    groups: dict[str, set[str]] = {}
    for path in PLAYLISTS:
        if not path.exists():
            continue
        entries = parse_entries(path.read_text(encoding="utf-8"))
        good = {e["url"] for e in entries if public_url(e["url"])}
        groups[path.name] = good
        urls |= good
    return sorted(urls), groups


def write_verified_only(checked: dict[str, str]) -> dict[str, int]:
    """Sólo publica una señal cuando la respuesta multimedia fue positiva.

    No retira nada de las listas principales: sirve una alternativa estricta
    para usuarios que prefieren menos canales con comprobación positiva reciente.
    """
    counts = {}
    for original, destination in VERIFIED_PLAYLISTS.items():
        if not original.exists():
            continue
        entries = parse_entries(original.read_text(encoding="utf-8"))
        lines = ["#EXTM3U"]
        kept = 0
        for entry in entries:
            if checked.get(entry["url"]) != "up":
                continue
            lines.append(entry["extinf"])
            lines.extend(entry["extras"])
            lines.append(entry["url"])
            kept += 1
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
        counts[destination.name] = kept
    return counts


def audit(max_workers: int, timeout: float, limit: int = 0) -> dict:
    urls, groups = load_urls()
    if limit > 0:
        urls = urls[:limit]
    if not urls:
        raise ValueError("No hay streams públicos que comprobar")
    state = load_state()
    today = datetime.now(timezone.utc).date().isoformat()
    results: Counter[str] = Counter()
    verified: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = {executor.submit(check_stream, url, timeout): url for url in urls}
        for future in as_completed(tasks):
            url = tasks[future]
            try:
                status, detail = future.result()
            except Exception as error:
                status, detail = "unknown", f"Error inesperado: {type(error).__name__}"
            key = url_key(url)
            state[key] = update_record(state.get(key, {}), status, detail, today)
            verified[url] = status
            results[status] += 1

    confirmed = sum(1 for item in state.values() if item.get("consecutive_down", 0) >= 2)
    per_group = {name: {
        "total": len(group),
        "up": sum(verified.get(url) == "up" for url in group),
        "down": sum(verified.get(url) == "down" for url in group),
        "unknown": sum(verified.get(url) == "unknown" for url in group),
    } for name, group in groups.items()}
    if not limit:
        verified_counts = write_verified_only(verified)
        STATE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        lines = [
            "# Auditoría de disponibilidad IPTV",
            "",
            f"Fecha UTC: {today}",
            f"URLs únicas probadas: {len(urls)}",
            f"Con segmento/manifiesto válido: {results['up']}",
            f"Fallo comprobado en esta pasada: {results['down']}",
            f"Indeterminado (timeout, geobloqueo u otros): {results['unknown']}",
            f"URLs con fallo reiterado confirmado: {confirmed}",
            "",
            "La prueba verifica acceso desde GitHub Actions, no reproducción mundial ni 24 horas continuas.",
            "Solamente se excluyen enlaces que fallan de forma concluyente en dos días de auditoría.",
            "",
            "## Listas con comprobación positiva reciente",
            "",
            *[f"- {name}: {count} entradas" for name, count in verified_counts.items()],
            "",
            "## Resultados por lista",
            "",
            "| Lista | Total | Accesibles | Fallo claro | Indeterminados |",
            "|---|---:|---:|---:|---:|",
        ]
        for name, counts in sorted(per_group.items()):
            lines.append(f"| {name} | {counts['total']} | {counts['up']} | {counts['down']} | {counts['unknown']} |")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"probados": len(urls), "up": results["up"],
                      "down": results["down"], "unknown": results["unknown"],
                      "exclusiones_confirmadas": confirmed}, ensure_ascii=False))
    return {"total": len(urls), "up": results["up"], "down": results["down"],
            "unknown": results["unknown"], "excluded": confirmed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--limit", type=int, default=0,
                        help="Solo para auditorías parciales: sin modificar el estado")
    opts = parser.parse_args()
    audit(max(1, min(opts.workers, 48)), max(2.0, min(opts.timeout, 15.0)), opts.limit)

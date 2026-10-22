from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
DEAD_FILE = Path(__file__).resolve().parent / "dead_urls.txt"
HEALTH_FILE = Path(__file__).resolve().parent / "salud_canales.json"
TARGETS = [
    Path(__file__).resolve().parent / "espanol.m3u",
    Path(__file__).resolve().parent / "por-pais.m3u",
    Path(__file__).resolve().parent / "por-categoria.m3u",
    Path(__file__).resolve().parent / "ecuador.m3u",
    Path(__file__).resolve().parent / "espanol-clasificado.m3u",
    Path(__file__).resolve().parent / "espanol-paises-y-categorias.m3u",
    ROOT / "tv.m3u",
    Path(__file__).resolve().parent / "24-7.m3u",
    Path(__file__).resolve().parent / "peliculas.m3u",
    Path(__file__).resolve().parent / "series.m3u",
]

dead = {
    line.strip()
    for line in DEAD_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
}

# Fallos repetidos y concluyentes del auditor. Los timeouts y 403 NO
# constituyen una razón suficiente para borrar un canal.
health = {}
if HEALTH_FILE.exists():
    health = json.loads(HEALTH_FILE.read_text(encoding="utf-8"))
confirmed_dead = {
    key for key, record in health.items()
    if record.get("consecutive_down", 0) >= 2
}

def filter_m3u(path: Path):
    if not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8").replace("\r", "").splitlines()
    out = []
    removed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("#EXTINF:"):
            out.append(line)
            i += 1
            continue
        block = [line]
        i += 1
        while i < len(lines) and lines[i].startswith("#") and not lines[i].startswith("#EXTINF:"):
            block.append(lines[i])
            i += 1
        if i < len(lines) and lines[i].startswith(("http://", "https://")):
            url = lines[i].strip()
            block.append(lines[i])
            i += 1
            if url in dead or hashlib.sha256(url.encode("utf-8")).hexdigest() in confirmed_dead:
                removed += 1
                continue
        out.extend(block)
    if len(lines) > 30 and removed > len([x for x in lines if x.startswith("#EXTINF:")]) * 0.35:
        raise ValueError(f"Exclusión de más del 35% de {path.name}: requiere revisión")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return removed

total = 0
for target in TARGETS:
    removed = filter_m3u(target)
    total += removed
    print(f"{target.name}: {removed} eliminados")
print(f"Total eliminado: {total}")

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEAD_FILE = Path(__file__).resolve().parent / "dead_urls.txt"
TARGETS = [
    Path(__file__).resolve().parent / "espanol.m3u",
    Path(__file__).resolve().parent / "por-pais.m3u",
    Path(__file__).resolve().parent / "por-categoria.m3u",
    Path(__file__).resolve().parent / "ecuador.m3u",
    Path(__file__).resolve().parent / "espanol-clasificado.m3u",
    Path(__file__).resolve().parent / "espanol-paises-y-categorias.m3u",
    ROOT / "tv.m3u",
]

dead = {
    line.strip()
    for line in DEAD_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
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
            if url in dead:
                removed += 1
                continue
        out.extend(block)
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return removed

total = 0
for target in TARGETS:
    removed = filter_m3u(target)
    total += removed
    print(f"{target.name}: {removed} eliminados")
print(f"Total eliminado: {total}")

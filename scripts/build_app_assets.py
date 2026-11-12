"""Fase 2 - prepara gli asset offline dell'app Flutter (app/assets/).

Da eseguire dopo ogni modifica di data/database.json o di assets/images/.

- app/assets/data/database.json: copia minificata del database, senza
  `data_completeness` (note interne in italiano, non destinate all'app).
- app/assets/images/thumb/<nome>.webp: immagine principale (images.primary),
  lato lungo 600 px, per card griglia/lista e righe del calendario.
- app/assets/images/full/<nome>.webp: tutte le immagini della galleria,
  lato lungo 1080 px, per il carosello della scheda alimento.

I file JPEG originali restano la fonte di verità in assets/images/.
Uso: python scripts/build_app_assets.py [--force] [--db-only]
    --db-only: aggiorna solo il database, senza toccare le immagini
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC_DB = ROOT / "data" / "database.json"
SRC_IMG = ROOT / "assets" / "images"
OUT = ROOT / "app" / "assets"
THUMB_PX, FULL_PX = 600, 1080
THUMB_Q, FULL_Q = 75, 80  # qualità approvata dall'utente (2026-11-06)
DROP_ITEM_KEYS = {"data_completeness"}


def webp_name(jpg: str) -> str:
    return Path(jpg).with_suffix(".webp").name


def convert(src: Path, dst: Path, max_side: int, quality: int, force: bool) -> None:
    if dst.exists() and not force and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "WEBP", quality=quality, method=4)


def main() -> None:
    force = "--force" in sys.argv
    db = json.loads(SRC_DB.read_text(encoding="utf-8"))
    primaries, gallery = set(), set()
    for item in db["items"]:
        for k in DROP_ITEM_KEYS:
            item.pop(k, None)
        imgs = item.get("images") or {}
        if imgs.get("primary"):
            primaries.add(imgs["primary"])
        gallery.update(imgs.get("gallery") or [])
        if imgs.get("primary"):
            gallery.add(imgs["primary"])

    out_db = OUT / "data" / "database.json"
    out_db.parent.mkdir(parents=True, exist_ok=True)
    out_db.write_text(json.dumps(db, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"database.json: {out_db.stat().st_size / 1e6:.1f} MB")
    for name in ("ui_copy.json", "ui_config.json"):  # testi e icone dell'app (admin_studio): copia identica byte per byte
        src = ROOT / "data" / name
        if src.exists():
            shutil.copyfile(src, OUT / "data" / name)
            print(f"{name} copiato")
    if "--db-only" in sys.argv:
        webp = {p.name for p in (OUT / "images").rglob("*.webp")}
        absent = sorted(f for f in gallery if webp_name(f) not in webp)
        if absent:
            print(f"{len(absent)} immagini del database non ancora convertite in WebP (in app: segnaposto)")
        return

    missing = [f for f in gallery if not (SRC_IMG / f).exists()]
    for f in sorted(primaries):
        if (SRC_IMG / f).exists():
            convert(SRC_IMG / f, OUT / "images" / "thumb" / webp_name(f), THUMB_PX, THUMB_Q, force)
    for f in sorted(gallery):
        if (SRC_IMG / f).exists():
            convert(SRC_IMG / f, OUT / "images" / "full" / webp_name(f), FULL_PX, FULL_Q, force)

    # Rimuove WebP orfani (immagini tolte dal database)
    keep = {"thumb": {webp_name(f) for f in primaries}, "full": {webp_name(f) for f in gallery}}
    for sub, names in keep.items():
        for p in (OUT / "images" / sub).glob("*.webp"):
            if p.name not in names:
                p.unlink()

    def size(p: Path) -> float:
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6

    print(f"thumb: {len(primaries)} file, {size(OUT / 'images' / 'thumb'):.1f} MB")
    print(f"full:  {len(gallery)} file, {size(OUT / 'images' / 'full'):.1f} MB")
    if missing:
        print("ATTENZIONE, immagini mancanti:", missing)


if __name__ == "__main__":
    main()

"""Phase 2 - prepares the offline assets of the Flutter app (app/assets/).

To run after every change to data/database.json or assets/images/.

- app/assets/data/database.json: minified copy of the database, without
  `data_completeness` (internal notes in Italian, not meant for the app).
- app/assets/images/thumb/<name>.webp: main image (images.primary),
  long side 600 px, for grid/list cards and calendar rows.
- app/assets/images/full/<name>.webp: all gallery images,
  long side 1080 px, for the product page carousel.

The original JPEG files remain the source of truth in assets/images/.
Usage: python scripts/build_app_assets.py [--force] [--db-only]
    --db-only: updates only the database, without touching the images
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
THUMB_Q, FULL_Q = 75, 80  # quality approved by the project owner (2026-11-06)
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
    for name in ("ui_copy.json", "ui_config.json"):  # app texts and icons (admin_studio): byte-for-byte identical copy
        src = ROOT / "data" / name
        if src.exists():
            shutil.copyfile(src, OUT / "data" / name)
            print(f"{name} copied")
    if "--db-only" in sys.argv:
        webp = {p.name for p in (OUT / "images").rglob("*.webp")}
        absent = sorted(f for f in gallery if webp_name(f) not in webp)
        if absent:
            print(f"{len(absent)} database images not yet converted to WebP (placeholder in the app)")
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

    print(f"thumb: {len(primaries)} files, {size(OUT / 'images' / 'thumb'):.1f} MB")
    print(f"full:  {len(gallery)} files, {size(OUT / 'images' / 'full'):.1f} MB")
    if missing:
        print("WARNING, missing images:", missing)


if __name__ == "__main__":
    main()

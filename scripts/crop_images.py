"""Standardises the image format (owner decision, 2026-11-06). Idempotent.

- Landscape photos (all types except botanical_plate): centred 3:2 crop.
- Botanical plates: all portrait 2:3, WITHOUT cropping: a margin in the paper colour (median of the
  border pixels) is added, so drawings and captions stay whole. The few landscape plates also become 2:3.
- Portrait or square photos that are not plates: untouched, except those in VERTICAL_ANCHOR (cropped to 3:2
  with the position chosen by the owner).
Before changing a file it saves the original in assets/images/_originals/ (only once), so changes can be
undone. Updates width/height in assets/images/_metadata.json; then run sync_images.py.
Usage:  python scripts/crop_images.py [--dry-run]
"""
import shutil
import statistics
import sys

from PIL import Image

from common import IMAGES, load_json, save_json

ORIG = IMAGES / "_originals"
# Portrait or square photos to bring to 3:2 anyway, with the vertical crop position chosen by the owner
# looking at the preview (0 = top part, 0.5 = centre, 1 = bottom part).
VERTICAL_ANCHOR = {
    "bietola_da_coste_swiss_chard_04.jpg": 0.5, "cavolfiore_cauliflower_02.jpg": 0.5, "cavolo_nero_black_kale_02.jpg": 0.5,
    "cavolo_verza_savoy_cabbage_02.jpg": 1.0, "finocchio_fennel_01.jpg": 0.5, "fungo_champignon_button_mushroom_05.jpg": 0.75,
    "fungo_pleurotus_oyster_mushroom_02.jpg": 0.5, "mango_mango_04.jpg": 0.5,
}
TOL = 0.01


def border_color(im):
    w, h = im.size
    px = im.load()
    pts = [px[x, y] for x in range(0, w, max(1, w // 60)) for y in (0, 1, h - 2, h - 1)]
    pts += [px[x, y] for y in range(0, h, max(1, h // 60)) for x in (0, 1, w - 2, w - 1)]
    return tuple(int(statistics.median(p[c] for p in pts)) for c in range(3))


def main():
    dry = "--dry-run" in sys.argv
    meta = load_json(IMAGES / "_metadata.json")
    cropped = padded = 0
    vertical = []
    for f in sorted(IMAGES.glob("*.jpg")):
        m = meta.get(f.name)
        if not m:
            continue
        im = Image.open(f).convert("RGB")
        w, h = im.size
        if m.get("view_type") == "botanical_plate":
            if abs(w / h - 2 / 3) <= TOL:
                continue
            nw, nh = (w, round(w * 3 / 2)) if w / h > 2 / 3 else (round(h * 2 / 3), h)
            nw, nh = max(nw, w), max(nh, h)
            out = Image.new("RGB", (nw, nh), border_color(im))
            out.paste(im, ((nw - w) // 2, (nh - h) // 2))
            padded += 1
        else:
            if h >= w and f.name not in VERTICAL_ANCHOR:
                vertical.append(f.name)
                continue
            if abs(w / h - 1.5) <= TOL:
                continue
            if w / h > 1.5:          # troppo larga: taglio ai lati
                nw = round(h * 1.5)
                box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
            else:                    # troppo alta (4:3, quadrata, verticale): taglio sopra e sotto
                nh = round(w / 1.5)
                top = round((h - nh) * VERTICAL_ANCHOR.get(f.name, 0.5))
                box = (0, top, w, top + nh)
            out = im.crop(box)
            cropped += 1
        if dry:
            continue
        ORIG.mkdir(exist_ok=True)
        if not (ORIG / f.name).exists():
            shutil.copy2(f, ORIG / f.name)
        out.save(f, "JPEG", quality=90, optimize=True, progressive=True)
        m["width"], m["height"] = out.size
    if not dry:
        save_json(IMAGES / "_metadata.json", meta)
    print(f"cropped to 3:2: {cropped}; plates brought to 2:3: {padded}; portrait photos left untouched: {len(vertical)} {vertical}"
          + (" (dry run)" if dry else ""))


if __name__ == "__main__":
    main()

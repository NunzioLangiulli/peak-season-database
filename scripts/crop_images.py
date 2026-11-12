"""Uniforma il formato delle immagini (decisione dell'utente, 2026-11-06). Idempotente.

- Foto orizzontali (tutti i tipi tranne botanical_plate): ritaglio centrato a 3:2.
- Tavole botaniche: tutte verticali 2:3, SENZA tagliare: si aggiunge un margine del colore della carta (mediana dei
  pixel del bordo), così disegni e didascalie restano interi. Anche le poche tavole orizzontali diventano 2:3.
- Foto verticali o quadrate che non sono tavole: non toccate, salvo quelle in VERTICAL_ANCHOR (ritagliate a 3:2
  con la posizione scelta dall'utente).
Prima di modificare un file ne salva l'originale in assets/images/_originals/ (una sola volta), così si può tornare
indietro. Aggiorna width/height in assets/images/_metadata.json; poi lanciare sync_images.py.
Uso:  python scripts/crop_images.py [--dry-run]
"""
import shutil
import statistics
import sys

from PIL import Image

from common import IMAGES, load_json, save_json

ORIG = IMAGES / "_originals"
# Foto verticali o quadrate da portare comunque a 3:2, con la posizione verticale del ritaglio decisa dall'utente
# guardando l'anteprima (0 = parte dall'alto, 0.5 = centro, 1 = parte più bassa).
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
    print(f"ritagliate a 3:2: {cropped}; tavole portate a 2:3: {padded}; foto verticali non toccate: {len(vertical)} {vertical}"
          + (" (prova)" if dry else ""))


if __name__ == "__main__":
    main()

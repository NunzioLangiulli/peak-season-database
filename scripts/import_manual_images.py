"""Importa le immagini scaricate a mano dall'utente (assets/images/_manual/), elencate in assets/images/_manual_list.json.

Per ogni file presente: lo converte in JPEG (sfondo bianco per le trasparenze), lo riduce a 1600 px al massimo, lo
salva come <id>_NN.jpg con il primo numero libero dell'alimento e ne scrive i metadati (autore, licenza, URL d'origine,
view_type) presi dalla candidata corrispondente; poi sposta l'originale in _manual/importate/.
Poi lanciare sync_images.py --renumber.
Uso:  python scripts/import_manual_images.py [--dry-run]
"""
import shutil
import sys

from PIL import Image

from common import IMAGES, load_json, save_json

MAN = IMAGES / "_manual"


def main():
    dry = "--dry-run" in sys.argv
    lst = load_json(IMAGES / "_manual_list.json")["files"]
    meta = load_json(IMAGES / "_metadata.json")
    done, missing = 0, []
    for name, info in lst.items():
        src = next((p for p in MAN.glob(name.rsplit(".", 1)[0] + ".*") if p.is_file()), None)
        if not src:
            missing.append(name)
            continue
        iid, cf = info["item"], info["candidate"]
        owner, fn = cf.split("/")
        t = fn.rsplit("_", 1)[0]
        h = next(x for x in load_json(IMAGES / "_candidates" / owner / "candidates.json")[t] if x["file"] == cf)
        used = {int(f.stem.rsplit("_", 1)[1]) for f in IMAGES.glob(f"{iid}_[0-9][0-9].jpg")}
        out = f"{iid}_{next(k for k in range(1, 100) if k not in used):02d}.jpg"
        print("importa", src.name, "->", out)
        done += 1
        if dry:
            continue
        im = Image.open(src)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, "white")
            bg.paste(im, mask=im.split()[3])
            im = bg
        im = im.convert("RGB")
        im.thumbnail((1600, 1600), Image.LANCZOS)
        im.save(IMAGES / out, "JPEG", quality=88, optimize=True, progressive=True)
        meta[out] = {"filename": out, "author": h["author"], "license": h["license"], "license_url": h.get("license_url"),
                     "source_url": h["source_url"], "provider": h["provider"], "width": im.width, "height": im.height, "view_type": t}
        (MAN / "importate").mkdir(exist_ok=True)
        shutil.move(str(src), str(MAN / "importate" / src.name))
        save_json(IMAGES / "_metadata.json", meta)
    print(f"importate {done}; ancora da scaricare: {len(missing)}")


if __name__ == "__main__":
    main()

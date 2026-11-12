"""Applica le scelte fatte nella pagina di revisione (assets/images/_candidates/image_selection.json).

- moves (lista in cima al file, facoltativa): sposta una foto già presente su un altro alimento e/o tipo,
  {"file": "<id>_NN.jpg", "to": "<altro_id>", "view_type": "<tipo>"}; prende il primo numero libero dell'alimento
  di destinazione e ne aggiorna i metadati (autore e licenza restano quelli originali);
- add: scarica la candidata alla risoluzione piena disponibile (Pixabay largeImageURL fino a 1280 px, riletto
  dall'API perché gli URL scadono dopo 24 h; Commons fino a 1600 px), la salva come <id>_NN.jpg con il numero libero
  successivo e ne scrive i metadati (autore, licenza, URL d'origine, view_type = tipo della candidata);
- add_from: come add, ma per una candidata trovata per un altro alimento,
  {"file": "<altro_id>/<tipo>_<n>.jpg", "view_type": "<tipo>"} (view_type facoltativo);
- remove: sposta la foto in assets/images/_removed/ (non la cancella) e ne toglie i metadati.
Poi lanciare sync_images.py (la principale diventa la prima foto full_frame).
Uso:  python scripts/apply_image_selection.py [--dry-run] [--selection altro_file.json]
"""
import io
import re
import shutil
import sys
import time

from PIL import Image

from common import IMAGES, SESSION, env, load_json, save_json

CAND = IMAGES / "_candidates"


def next_free(iid, used):
    if iid not in used:
        used[iid] = {int(f.stem.rsplit("_", 1)[1]) for f in IMAGES.glob(f"{iid}_[0-9][0-9].jpg")}
    n = next(k for k in range(1, 100) if k not in used[iid])
    used[iid].add(n)
    return f"{iid}_{n:02d}.jpg"


def download(h):
    url = h["full"]
    if h["provider"] == "pixabay":   # gli URL immagine di Pixabay scadono dopo 24 h: si rilegge l'URL dall'API
        m = re.search(r"-(\d+)/?$", h["source_url"].split("?")[0])
        hit = SESSION.get("https://pixabay.com/api/", params={"key": env("PIXABAY_API_KEY"), "id": m.group(1)},
                          timeout=60).json().get("hits") or []
        if not hit:
            raise RuntimeError("non più disponibile su Pixabay")
        url = hit[0]["largeImageURL"]
    if h["provider"] == "wikimedia_commons" and "/thumb/" in url:   # file originale: niente miniature da generare
        url = url.replace("/thumb/", "/").rsplit("/", 1)[0]
    for attempt in range(5):
        r = SESSION.get(url, timeout=90)
        if r.status_code != 429:
            break
        time.sleep(20 * (attempt + 1))   # Wikimedia limita le richieste ravvicinate
    r.raise_for_status()
    if h["provider"] == "wikimedia_commons":
        time.sleep(6)
    im = Image.open(io.BytesIO(r.content))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[3])
        im = bg
    im = im.convert("RGB")
    im.thumbnail((1600, 1600), Image.LANCZOS)
    return im


def main():
    dry = "--dry-run" in sys.argv
    data = load_json(CAND / (sys.argv[sys.argv.index("--selection") + 1] if "--selection" in sys.argv else "image_selection.json"))
    sel = data["items"]
    cand = load_json(CAND / "candidates.json")["items"]
    meta = load_json(IMAGES / "_metadata.json")
    removed = IMAGES / "_removed"
    used = {}
    n_add = n_rem = n_mov = 0
    failed = []
    for mv in data.get("moves", []):
        src = mv["file"]
        if not (IMAGES / src).exists():
            print("  foto da spostare non trovata:", src)
            continue
        dst = next_free(mv["to"], used)
        print("sposta", src, "->", dst, mv.get("view_type", ""))
        n_mov += 1
        if not dry:
            (IMAGES / src).rename(IMAGES / dst)
            m = meta.pop(src, {})
            meta[dst] = {**m, "filename": dst, "view_type": mv.get("view_type", m.get("view_type"))}
            meta[dst].pop("flags", None)
            meta[dst].pop("variety", None)
    for iid, s in sel.items():
        for fn in s.get("remove", []):
            if (IMAGES / fn).exists():
                print("togli", fn)
                if not dry:
                    removed.mkdir(exist_ok=True)
                    shutil.move(str(IMAGES / fn), str(removed / fn))
                    meta.pop(fn, None)
                n_rem += 1
        jobs = [(cf, None) for cf in s.get("add", [])] + [(x["file"], x.get("view_type")) for x in s.get("add_from", [])]
        for cf, vt in jobs:
            owner = cf.split("/", 1)[0]
            by_file = {h["file"]: (t, h) for t, lst in cand.get(owner, {}).items() if not t.startswith("_") for h in lst}
            if cf not in by_file:
                print("  candidata sconosciuta:", cf)
                continue
            t, h = by_file[cf]
            fn = next_free(iid, used)
            print("aggiungi", cf, "->", fn, vt or t)
            n_add += 1
            if dry:
                continue
            try:
                im = download(h)
            except Exception as e:
                print("  ERRORE", cf, e)
                failed.append(cf)
                used[iid].discard(int(fn[-6:-4]))
                n_add -= 1
                continue
            im.save(IMAGES / fn, "JPEG", quality=88, optimize=True, progressive=True)
            meta[fn] = {"filename": fn, "author": h["author"], "license": h["license"], "license_url": h.get("license_url"),
                        "source_url": h["source_url"], "provider": h["provider"], "width": im.width, "height": im.height,
                        "view_type": vt or t}
        if not dry:
            save_json(IMAGES / "_metadata.json", meta)   # salva dopo ogni alimento
    if not dry:
        save_json(IMAGES / "_metadata.json", meta)
    print(f"spostate {n_mov}, aggiunte {n_add}, tolte {n_rem}" + (" (prova)" if dry else ""))
    if failed:
        print("non scaricate:", failed)


if __name__ == "__main__":
    main()

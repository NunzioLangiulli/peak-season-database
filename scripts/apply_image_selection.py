"""Applies the choices made on the review page (assets/images/_candidates/image_selection.json).

- moves (list at the top of the file, optional): moves an existing photo to another product and/or type,
  {"file": "<id>_NN.jpg", "to": "<other_id>", "view_type": "<type>"}; takes the first free number of the target
  product and updates its metadata (author and licence stay the original ones);
- add: downloads the candidate at the full available resolution (Pixabay largeImageURL up to 1280 px, re-read
  from the API because URLs expire after 24 h; Commons up to 1600 px), saves it as <id>_NN.jpg with the next free
  number and writes its metadata (author, licence, source URL, view_type = type of the candidate);
- add_from: like add, but for a candidate found for another product,
  {"file": "<other_id>/<type>_<n>.jpg", "view_type": "<type>"} (view_type optional);
- remove: moves the photo to assets/images/_removed/ (does not delete it) and removes its metadata.
Then run sync_images.py (the main photo becomes the first full_frame photo).
Usage:  python scripts/apply_image_selection.py [--dry-run] [--selection other_file.json]
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
    if h["provider"] == "pixabay":   # Pixabay image URLs expire after 24 h: the URL is re-read from the API
        m = re.search(r"-(\d+)/?$", h["source_url"].split("?")[0])
        hit = SESSION.get("https://pixabay.com/api/", params={"key": env("PIXABAY_API_KEY"), "id": m.group(1)},
                          timeout=60).json().get("hits") or []
        if not hit:
            raise RuntimeError("non più disponibile su Pixabay")
        url = hit[0]["largeImageURL"]
    if h["provider"] == "wikimedia_commons" and "/thumb/" in url:   # original file: no thumbnails to generate
        url = url.replace("/thumb/", "/").rsplit("/", 1)[0]
    for attempt in range(5):
        r = SESSION.get(url, timeout=90)
        if r.status_code != 429:
            break
        time.sleep(20 * (attempt + 1))   # Wikimedia throttles rapid requests
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
            save_json(IMAGES / "_metadata.json", meta)   # save after every product
    if not dry:
        save_json(IMAGES / "_metadata.json", meta)
    print(f"spostate {n_mov}, aggiunte {n_add}, tolte {n_rem}" + (" (prova)" if dry else ""))
    if failed:
        print("non scaricate:", failed)


if __name__ == "__main__":
    main()

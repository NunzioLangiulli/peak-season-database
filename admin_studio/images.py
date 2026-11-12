"""Scheda Immagini dell'Admin Studio: galleria di ogni prodotto, foto principale, tipo di vista e download da URL.

Le foto stanno in assets/images/<id>_NN.jpg; i metadati di licenza in assets/images/_metadata.json (fonte per
scripts/sync_images.py) e nel database (images.primary, images.gallery, images.image_details). Lo studio aggiorna
entrambi. La foto principale scelta a mano è registrata in assets/images/_primary_manual.json, che sync_images.py
rispetta: altrimenti la regola automatica (prima foto "full_frame") la cambierebbe al primo riallineamento.

Download: si incolla l'URL di una pagina Wikimedia Commons (File:...), di un file upload.wikimedia.org, di una pagina
o foto USDA ARS, o di un'immagine qualsiasi. Per Wikimedia autore, licenza e pagina sorgente vengono dall'API di
Commons; per USDA ARS la licenza è il pubblico dominio delle foto del governo USA (autore dalla didascalia "Photo by").
Per le altre fonti autore e licenza vanno scritti nel modulo: senza licenza la foto non entra nella galleria.
"""
import html
import io
import json
import re
import urllib.parse
import time
from pathlib import Path

from common import DATA, IMAGES, SESSION, load_json, save_json

META = IMAGES / "_metadata.json"
MANUAL = IMAGES / "_primary_manual.json"
VIEW_TYPES = ["full_frame", "isolated_background", "plant_in_field", "botanical_plate", "cut_section", "other"]
MAX_BYTES = 40 * 1024 * 1024
MAX_SIDE = 2400
WIKI_WIDTH = 1920                                     # misura standard delle miniature Wikimedia (le altre possono dare 429)


def _db():
    return load_json(DATA / "database.json")


def item_list():
    out = []
    for it in _db()["items"]:
        im = it["images"]
        out.append({"id": it["id"], "name": it["names"]["it"], "name_en": it["names"]["en"], "category": it.get("category"),
                    "count": len(im.get("gallery") or []), "primary": im.get("primary")})
    return out


def links(it):
    sci = it["botany"].get("scientific_name") or ""
    en = it["names"]["en"]
    q = urllib.parse.quote_plus
    return [
        {"label": f"Wikimedia Commons · {sci}", "url": f"https://commons.wikimedia.org/w/index.php?search={q(sci)}&title=Special:MediaSearch&type=image"},
        {"label": f"Wikimedia Commons · {en}", "url": f"https://commons.wikimedia.org/w/index.php?search={q(en)}&title=Special:MediaSearch&type=image"},
        {"label": f"USDA ARS Image Gallery · {en}", "url": f"https://www.ars.usda.gov/search/?q={q(en + ' image')}"},
        {"label": f"USDA ARS (ricerca immagini web) · {en}", "url": f"https://www.google.com/search?tbm=isch&q={q('site:ars.usda.gov ' + en)}"},
    ]


def item_detail(iid):
    it = next((x for x in _db()["items"] if x["id"] == iid), None)
    if not it:
        return {"error": "prodotto non trovato"}
    im = it["images"]
    det = {d["filename"]: d for d in im.get("image_details") or []}
    manual = load_json(MANUAL) if MANUAL.exists() else {}
    return {"id": iid, "name": it["names"]["it"], "name_en": it["names"]["en"], "scientific_name": it["botany"].get("scientific_name"),
            "primary": im.get("primary"), "primary_manual": manual.get(iid), "view_types": VIEW_TYPES, "links": links(it),
            "images": [det.get(f, {"filename": f}) for f in im.get("gallery") or []]}


def save(data):
    """Foto principale e tipi di vista di un prodotto."""
    db = _db()
    it = next(x for x in db["items"] if x["id"] == data["id"])
    im = it["images"]
    meta = load_json(META) if META.exists() else {}
    vt = data.get("view_types") or {}
    for d in im.get("image_details") or []:
        if d["filename"] in vt:
            if vt[d["filename"]] not in VIEW_TYPES:
                raise ValueError(f"tipo di vista non valido: {vt[d['filename']]}")
            d["view_type"] = vt[d["filename"]]
            if d["filename"] in meta:
                meta[d["filename"]]["view_type"] = d["view_type"]
    p = data.get("primary")
    if p and p != im.get("primary"):
        if p not in (im.get("gallery") or []):
            raise ValueError("la foto principale deve essere nella galleria")
        im["primary"] = p
        im["gallery"] = [p] + [f for f in im["gallery"] if f != p]
        manual = load_json(MANUAL) if MANUAL.exists() else {}
        manual[it["id"]] = p
        save_json(MANUAL, manual)
    save_json(META, meta)
    save_json(DATA / "database.json", db)


# ------------------------------------------------------------------ download
def _get(url, accept="*/*"):
    """Scarica con il client del progetto (common.SESSION: TLS verificato, User-Agent del progetto). Wikimedia risponde
    429 ai client generici; se chiede di aspettare (Retry-After) si riprova una volta."""
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise ValueError("serve un indirizzo http o https")
    for attempt in range(2):
        r = SESSION.get(url, headers={"Accept": accept}, timeout=40, stream=True)
        if r.status_code == 429 and attempt == 0:
            time.sleep(min(int(r.headers.get("Retry-After") or 5), 15))
            continue
        r.raise_for_status()
        data = r.raw.read(MAX_BYTES + 1, decode_content=True)
        if len(data) > MAX_BYTES:
            raise ValueError("file troppo grande (oltre 40 MB)")
        return data, r.headers.get("Content-Type", "").split(";")[0].strip(), r.url
    raise ValueError("il sito chiede di riprovare più tardi (troppe richieste)")


def _strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _commons(title):
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|extmetadata"
           f"&iiurlwidth={WIKI_WIDTH}&titles=" + urllib.parse.quote(title))
    data, _, _ = _get(api, "application/json")
    page = next(iter(json.loads(data)["query"]["pages"].values()))
    if "imageinfo" not in page:
        raise ValueError(f"file non trovato su Wikimedia Commons: {title}")
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata") or {}
    v = lambda k: _strip((em.get(k) or {}).get("value"))  # noqa: E731
    big = ii.get("width", 0) > WIKI_WIDTH
    return {"image_url": ii.get("thumburl") if big and ii.get("thumburl") else ii["url"], "source_url": ii.get("descriptionurl"),
            "author": v("Artist") or v("Credit") or None, "license": v("LicenseShortName") or None,
            "license_url": v("LicenseUrl") or None, "provider": "wikimedia_commons"}


def resolve(url):
    """Indirizzo della foto e metadati (quando la fonte li espone)."""
    u = urllib.parse.urlparse(url.strip())
    host, path = u.netloc.lower(), urllib.parse.unquote(u.path)
    if host.endswith("wikimedia.org") or host.endswith("wikipedia.org"):
        if "/wiki/" in path and ("File:" in path or "Image:" in path):
            return _commons("File:" + path.split(":", 1)[1])
        if host == "upload.wikimedia.org":
            parts = path.split("/")
            name = parts[-2] if "/thumb/" in path else parts[-1]
            return _commons("File:" + name)
        if "media" in u.fragment:                   # .../wiki/Pagina#/media/File:Nome.jpg
            return _commons("File:" + urllib.parse.unquote(u.fragment).split("File:", 1)[1])
    info = {"image_url": url, "source_url": url, "author": None, "license": None, "license_url": None,
            "provider": "usda_ars" if "usda.gov" in host else "user"}
    data, ctype, final = _get(url)
    if ctype.startswith("image/"):
        info["_bytes"] = data
        return info
    page = data.decode("utf-8", "replace")
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page) or \
        re.search(r'<img[^>]+src=["\']([^"\']+\.(?:jpe?g|png|webp))', page, re.I)
    if not m:
        raise ValueError("nella pagina non ho trovato un'immagine: incolla l'indirizzo diretto della foto")
    info["image_url"] = urllib.parse.urljoin(final, html.unescape(m.group(1)))
    if info["provider"] == "usda_ars":
        by = re.search(r"[Pp]hoto(?:graph)? by ([A-Z][\w.\- ]{2,60}?)[.<,)]", page)
        info.update({"author": f"{by.group(1).strip()} / USDA ARS" if by else "USDA Agricultural Research Service",
                     "license": "Public domain (USDA ARS)", "license_url": "https://www.ars.usda.gov/oc/images/image-gallery/"})
    return info


def next_name(iid, gallery):
    used = {int(m.group(1)) for f in list(gallery) + [p.name for p in IMAGES.glob(f"{iid}_*.jpg")]
            if (m := re.fullmatch(re.escape(iid) + r"_(\d{2})\.jpg", f))}
    n = max(used, default=0) + 1
    if n > 99:
        raise ValueError("questo prodotto ha già 99 foto")
    return f"{iid}_{n:02d}.jpg"


def download(data):
    from PIL import Image, ImageOps
    db = _db()
    it = next(x for x in db["items"] if x["id"] == data["id"])
    info = resolve(data["url"])
    for k in ("author", "license", "license_url"):
        if (data.get(k) or "").strip():
            info[k] = data[k].strip()                # quello scritto nel modulo vale più di quello letto dalla fonte
    if not info.get("author") or not info.get("license"):
        raise ValueError("autore e licenza non sono leggibili da questa fonte: scrivili nel modulo (servono per mostrare la foto)")
    raw = info.pop("_bytes", None) or _get(info["image_url"], "image/*")[0]
    with Image.open(io.BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        name = next_name(it["id"], it["images"].get("gallery") or [])
        dst = IMAGES / name
        im.save(dst, "JPEG", quality=90, optimize=True)
        w, h = im.size
    vt = data.get("view_type") if data.get("view_type") in VIEW_TYPES else "full_frame"
    detail = {"filename": name, "author": info["author"][:300], "license": info["license"], "license_url": info.get("license_url"),
              "source_url": info.get("source_url") or data["url"], "provider": info["provider"], "width": w, "height": h, "view_type": vt}
    meta = load_json(META) if META.exists() else {}
    meta[name] = detail
    save_json(META, meta)
    imgs = it["images"]
    imgs.setdefault("gallery", []).append(name)
    imgs.setdefault("image_details", []).append(dict(detail))
    if data.get("make_primary") or not imgs.get("primary"):
        imgs["primary"] = name
        imgs["gallery"] = [name] + [f for f in imgs["gallery"] if f != name]
        manual = load_json(MANUAL) if MANUAL.exists() else {}
        manual[it["id"]] = name
        save_json(MANUAL, manual)
    save_json(DATA / "database.json", db)
    return {"new_files": [str(dst)], "added": detail}

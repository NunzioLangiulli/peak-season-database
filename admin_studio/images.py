"""Images tab of the Admin Studio: gallery of each product, main photo, view type and download from URL.

Photos live in assets/images/<id>_NN.jpg; licence metadata in assets/images/_metadata.json (source for
scripts/sync_images.py) and in the database (images.primary, images.gallery, images.image_details). The Studio updates
both. The main photo chosen by hand is recorded in assets/images/_primary_manual.json, which sync_images.py
respects: otherwise the automatic rule (first "full_frame" photo) would change it at the first realignment.

Download: paste the URL of a Wikimedia Commons page (File:...), of an upload.wikimedia.org file, of a USDA ARS
page or photo, or of any image. For Wikimedia, author, licence and source page come from the Commons
API; for USDA ARS the licence is the public domain of US government photos (author from the "Photo by" caption).
For other sources author and licence must be entered in the form: without a licence the photo does not enter the gallery.
"""
import html
import io
import json
import re
import urllib.parse
import time
from pathlib import Path

from common import DATA, IMAGES, SESSION, load_json, null_paths, save_json

META = IMAGES / "_metadata.json"
MANUAL = IMAGES / "_primary_manual.json"
REMOVED = IMAGES / "_removed"                         # deleted photos are moved here (as scripts/apply_image_selection.py does)
ORIGINALS = IMAGES / "_originals"                     # uncropped originals, as scripts/crop_images.py keeps them
VIEW_TYPES = ["full_frame", "isolated_background", "plant_in_field", "botanical_plate", "cut_section", "other"]
MAX_BYTES = 40 * 1024 * 1024
MAX_SIDE = 2400
WIKI_WIDTH = 1920                                     # standard Wikimedia thumbnail size (other sizes may return 429)


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
        {"label": f"USDA ARS (web image search) · {en}", "url": f"https://www.google.com/search?tbm=isch&q={q('site:ars.usda.gov ' + en)}"},
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
            "images": [{**det.get(f, {"filename": f}), "v": _version(f)} for f in im.get("gallery") or []]}


def _version(name):
    """Changes whenever the file behind a name changes: the browser reloads instead of showing a cached photo."""
    p = IMAGES / name
    return int(p.stat().st_mtime) if p.exists() else 0


def _align(im):
    """image_details in the same order as the gallery (validate_db requires it; the primary photo comes first)."""
    det = {d["filename"]: d for d in im.get("image_details") or []}
    im["image_details"] = [det[f] for f in im.get("gallery") or [] if f in det]


def save(data):
    """Main photo, gallery order and view types of a product."""
    db = _db()
    it = next(x for x in db["items"] if x["id"] == data["id"])
    im = it["images"]
    meta = load_json(META) if META.exists() else {}
    vt = data.get("view_types") or {}
    for d in im.get("image_details") or []:
        if d["filename"] in vt:
            if vt[d["filename"]] not in VIEW_TYPES:
                raise ValueError(f"invalid view type: {vt[d['filename']]}")
            d["view_type"] = vt[d["filename"]]
            if d["filename"] in meta:
                meta[d["filename"]]["view_type"] = d["view_type"]
    gal = im.get("gallery") or []
    order = data.get("order")
    if order and order != gal:
        # the gallery order chosen by hand (sync_images.py keeps it); the first photo is the primary one
        if sorted(order) != sorted(gal):
            raise ValueError("the new order must contain exactly the photos of the gallery")
        p = order[0]
    else:
        order, p = None, data.get("primary")
    if order or (p and p != im.get("primary")):
        if p not in gal:
            raise ValueError("the primary photo must be in the gallery")
        im["primary"] = p
        im["gallery"] = list(order) if order else [p] + [f for f in gal if f != p]
        _align(im)
        manual = load_json(MANUAL) if MANUAL.exists() else {}   # recorded also on a pure reorder: without it
        manual[it["id"]] = p                                  # sync_images.py would pick the first "whole" photo
        save_json(MANUAL, manual)
    save_json(META, meta)
    save_json(DATA / "database.json", db)


# ------------------------------------------------------------------ download
def _get(url, accept="*/*"):
    """Downloads with the project client (common.SESSION: verified TLS, project User-Agent). Wikimedia returns
    429 to generic clients; if it asks to wait (Retry-After) it retries once."""
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise ValueError("an http or https address is required")
    for attempt in range(2):
        r = SESSION.get(url, headers={"Accept": accept}, timeout=40, stream=True)
        if r.status_code == 429 and attempt == 0:
            time.sleep(min(int(r.headers.get("Retry-After") or 5), 15))
            continue
        r.raise_for_status()
        data = r.raw.read(MAX_BYTES + 1, decode_content=True)
        if len(data) > MAX_BYTES:
            raise ValueError("file too large (over 40 MB)")
        return data, r.headers.get("Content-Type", "").split(";")[0].strip(), r.url
    raise ValueError("the site asks to retry later (too many requests)")


def _strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _commons(title):
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|extmetadata"
           f"&iiurlwidth={WIKI_WIDTH}&titles=" + urllib.parse.quote(title))
    data, _, _ = _get(api, "application/json")
    page = next(iter(json.loads(data)["query"]["pages"].values()))
    if "imageinfo" not in page:
        raise ValueError(f"file not found on Wikimedia Commons: {title}")
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata") or {}
    v = lambda k: _strip((em.get(k) or {}).get("value"))  # noqa: E731
    big = ii.get("width", 0) > WIKI_WIDTH
    return {"image_url": ii.get("thumburl") if big and ii.get("thumburl") else ii["url"], "source_url": ii.get("descriptionurl"),
            "author": v("Artist") or v("Credit") or None, "license": v("LicenseShortName") or None,
            "license_url": v("LicenseUrl") or None, "provider": "wikimedia_commons"}


def resolve(url):
    """Photo address and metadata (when the source exposes them)."""
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
        raise ValueError("no image found on the page: paste the direct address of the photo")
    info["image_url"] = urllib.parse.urljoin(final, html.unescape(m.group(1)))
    if info["provider"] == "usda_ars":
        by = re.search(r"[Pp]hoto(?:graph)? by ([A-Z][\w.\- ]{2,60}?)[.<,)]", page)
        info.update({"author": f"{by.group(1).strip()} / USDA ARS" if by else "USDA Agricultural Research Service",
                     "license": "Public domain (USDA ARS)", "license_url": "https://www.ars.usda.gov/oc/images/image-gallery/"})
    return info


def next_name(iid, gallery):
    """Next free <id>_NN.jpg. Numbers of deleted photos (assets/images/_removed/) and of any metadata entry are never
    reused: a reused name would show the old photo from browser and WebP caches, and _originals/ would hold the wrong one."""
    names = list(gallery) + [p.name for p in IMAGES.glob(f"{iid}_*.jpg")] + [p.name for p in REMOVED.glob(f"{iid}_*.jpg")]
    names += [k for k in (load_json(META) if META.exists() else {}) if k.startswith(iid + "_")]
    used = {int(m.group(1)) for f in names if (m := re.match(re.escape(iid) + r"_(\d{2})(?:\.|_)", f))}
    n = max(used, default=0) + 1
    if n > 99:
        raise ValueError("this product already has 99 photos")
    return f"{iid}_{n:02d}.jpg"


_FETCHED = {}                                         # url -> (time, info, bytes): the preview's download is reused when adding


def _url_info(url):
    hit = _FETCHED.get(url)
    if hit and time.time() - hit[0] < 900:
        return dict(hit[1])
    info = resolve(url)
    _FETCHED[url] = (time.time(), dict(info), None)
    return info


def _url_bytes(url, info):
    hit = _FETCHED.get(url)
    if hit and hit[2] is not None and time.time() - hit[0] < 900:
        return hit[2]
    raw = info.pop("_bytes", None) or _get(info["image_url"], "image/*")[0]
    info.pop("_bytes", None)
    _FETCHED.clear()                                  # keep only the latest photo in memory
    _FETCHED[url] = (time.time(), {k: v for k, v in info.items() if k != "_bytes"}, raw)
    return raw


def download(data):
    db = _db()
    it = next(x for x in db["items"] if x["id"] == data["id"])
    info = _url_info(data["url"])
    for k in ("author", "license", "license_url"):
        if (data.get(k) or "").strip():
            info[k] = data[k].strip()                # what is typed in the form beats what is read from the source
    if not info.get("author") or not info.get("license"):
        raise ValueError("author and licence cannot be read from this source: type them in the form (they are needed to show the photo)")
    raw = _url_bytes(data["url"], info)
    return _add(db, it, raw, info, data)


def _data_url_bytes(data_url):
    import base64
    m = re.match(r"data:image/(?:jpeg|png|webp);base64,(.+)", data_url or "", re.S)
    if not m:
        raise ValueError("choose a JPG, PNG or WebP photo")
    raw = base64.b64decode(m.group(1))
    if len(raw) > MAX_BYTES:
        raise ValueError("file too large (over 40 MB)")
    return raw


def upload(data):
    """A photo file from the computer (data URL), with author and licence typed in the form."""
    db = _db()
    it = next(x for x in db["items"] if x["id"] == data["id"])
    raw = _data_url_bytes(data.get("data_url"))
    info = {k: (data.get(k) or "").strip() or None for k in ("author", "license", "license_url", "source_url")}
    if not info["author"] or not info["license"]:
        raise ValueError("author and licence are needed to show the photo in the app")
    info["provider"] = "user"
    # own photo without a web page: source_url stays empty (the app shows author and licence only)
    return _add(db, it, raw, info, data)


IMAGE_FIELDS = {"images.primary", "images.gallery", "images.image_details"}


def _completeness(it):
    """Keeps data_completeness in step with the photos, as sync_images.py does: the first photo fills
    images.primary (no longer missing), removing the last one empties it again."""
    dc = it["data_completeness"]
    dc["missing_fields"] = null_paths(it)
    enr = set(dc["fields_enriched_via_scraping"])
    enr = enr | IMAGE_FIELDS if it["images"].get("gallery") else enr - IMAGE_FIELDS
    dc["fields_enriched_via_scraping"] = sorted(enr)
    if dc["missing_fields"]:
        dc["is_complete"] = False


def _add(db, it, raw, info, data):
    vt = data.get("view_type") if data.get("view_type") in VIEW_TYPES else "full_frame"
    src = _open(raw)
    out, how = standardise(src, vt, data.get("crop"))
    name = next_name(it["id"], it["images"].get("gallery") or [])
    dst = IMAGES / name
    out.save(dst, "JPEG", quality=90, optimize=True, progressive=True)
    w, h = out.size
    new = [str(dst)]
    if how["changed"]:                               # the uncropped photo, like crop_images.py does
        ORIGINALS.mkdir(exist_ok=True)
        src.save(ORIGINALS / name, "JPEG", quality=90, optimize=True, progressive=True)
        new.append(str(ORIGINALS / name))
    detail = {"filename": name, "author": info["author"][:300], "license": info["license"], "license_url": info.get("license_url"),
              "source_url": info.get("source_url") or data.get("url"), "provider": info["provider"], "width": w, "height": h, "view_type": vt}
    meta = load_json(META) if META.exists() else {}
    meta[name] = detail
    save_json(META, meta)
    imgs = it["images"]
    imgs.setdefault("gallery", []).append(name)
    imgs.setdefault("image_details", []).append(dict(detail))
    if data.get("make_primary") or not imgs.get("primary"):
        imgs["primary"] = name
        imgs["gallery"] = [name] + [f for f in imgs["gallery"] if f != name]
        _align(imgs)
        manual = load_json(MANUAL) if MANUAL.exists() else {}
        manual[it["id"]] = name
        save_json(MANUAL, manual)
    _completeness(it)
    save_json(DATA / "database.json", db)
    return {"new_files": new, "added": detail, "crop": how["text"]}


# ------------------------------------------------------------------ format rules (scripts/crop_images.py)
def _open(raw):
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        return im.copy()


def standardise(im, view_type, crop=None):
    """The owner's format rules of scripts/crop_images.py (2026-11-06):
    - botanical plates: portrait 2:3 WITHOUT cropping, margin in the paper colour;
    - other landscape photos: centred 3:2 crop;
    - portrait or square photos: left whole, unless crop = {"mode": "crop", "anchor": 0..1} asks for a 3:2 crop
      (0 = keep the top part, 0.5 = centre, 1 = bottom part), as VERTICAL_ANCHOR does in crop_images.py.
    Returns (image, {"changed", "text", "options"})."""
    from PIL import Image
    from crop_images import TOL, border_color
    crop = crop or {}
    w, h = im.size
    if view_type == "botanical_plate":
        if abs(w / h - 2 / 3) <= TOL:
            return im, {"changed": False, "text": "Plate already 2:3: unchanged", "options": False}
        nw, nh = (w, round(w * 3 / 2)) if w / h > 2 / 3 else (round(h * 2 / 3), h)
        nw, nh = max(nw, w), max(nh, h)
        out = Image.new("RGB", (nw, nh), border_color(im))
        out.paste(im, ((nw - w) // 2, (nh - h) // 2))
        return out, {"changed": True, "text": f"Plate brought to 2:3 with a paper-coloured margin ({w}×{h} → {nw}×{nh}), nothing cut", "options": False}
    if h >= w and crop.get("mode") != "crop":
        return im, {"changed": False, "text": "Portrait or square photo: kept whole (you can crop it to 3:2)", "options": True}
    if abs(w / h - 1.5) <= TOL:
        return im, {"changed": False, "text": "Already 3:2: unchanged", "options": h >= w}
    if w / h > 1.5:
        nw = round(h * 1.5)
        box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
        text = "Centred 3:2 crop (sides trimmed)"
    else:
        nh = round(w / 1.5)
        a = min(1.0, max(0.0, float(crop.get("anchor", 0.5))))
        top = round((h - nh) * a)
        box = (0, top, w, top + nh)
        text = "3:2 crop (top and bottom trimmed)" if h < w else f"3:2 crop of a portrait photo, keeping the {'top' if a < .34 else 'bottom' if a > .66 else 'centre'}"
    out = im.crop(box)
    return out, {"changed": True, "text": f"{text}: {w}×{h} → {out.size[0]}×{out.size[1]}", "options": h >= w}


def _small(im, side=520):
    import base64
    t = im.copy()
    t.thumbnail((side, side))
    b = io.BytesIO()
    t.save(b, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def preview(data):
    """Before/after of the format rules for a photo about to be added (URL or uploaded file); nothing is saved."""
    vt = data.get("view_type") if data.get("view_type") in VIEW_TYPES else "full_frame"
    if data.get("data_url"):
        raw, info = _data_url_bytes(data["data_url"]), {}
    else:
        info = _url_info(data["url"])
        raw = _url_bytes(data["url"], info)
    src = _open(raw)
    out, how = standardise(src, vt, data.get("crop"))
    return {"before": _small(src), "after": _small(out), "size_before": src.size, "size_after": out.size, **how,
            "author": info.get("author"), "license": info.get("license")}


# ------------------------------------------------------------------ delete
def photo_path(iid, name):
    """Original of a product photo (only <id>_NN.jpg names of that product)."""
    if not re.fullmatch(re.escape(iid) + r"_\d{2}\.jpg", name or ""):
        raise ValueError(f"not a photo of {iid}: {name}")
    return IMAGES / name


def delete(data):
    """Removes a photo: original file, _metadata.json entry, gallery/image_details and the manual primary choice.
    The caller (studio.guarded) has already backed up the file, so a failed validation puts everything back.
    If the deleted photo was the primary one, the automatic rule of sync_images.py picks the new one
    (first "full_frame" photo without flags or variety, otherwise the first photo)."""
    db = _db()
    it = next(x for x in db["items"] if x["id"] == data["id"])
    name = data["filename"]
    path = photo_path(it["id"], name)
    im = it["images"]
    if name not in (im.get("gallery") or []):
        raise ValueError(f"{name} is not in the gallery of {it['id']}")
    meta = load_json(META) if META.exists() else {}
    meta.pop(name, None)
    manual = load_json(MANUAL) if MANUAL.exists() else {}
    if manual.get(it["id"]) == name:
        manual.pop(it["id"])
    im["gallery"] = [f for f in im["gallery"] if f != name]
    im["image_details"] = [d for d in im.get("image_details") or [] if d["filename"] != name]
    if im.get("primary") == name or im.get("primary") not in im["gallery"]:
        det = {d["filename"]: d for d in im["image_details"]}
        ff = [f for f in im["gallery"] if det.get(f, {}).get("view_type") == "full_frame"
              and not det[f].get("flags") and not det[f].get("variety")]
        im["primary"] = (ff or im["gallery"] or [None])[0]
        if im["primary"]:
            im["gallery"] = [im["primary"]] + [f for f in im["gallery"] if f != im["primary"]]
    _align(im)
    _completeness(it)
    save_json(META, meta)
    save_json(MANUAL, manual)
    save_json(DATA / "database.json", db)
    if path.exists():                                # kept in assets/images/_removed/ (not on Git), as the scripts do
        REMOVED.mkdir(exist_ok=True)
        dst = REMOVED / name
        if dst.exists():
            dst = REMOVED / f"{path.stem}_{int(time.time())}.jpg"
        path.replace(dst)
        moved = [str(dst)]
        if (ORIGINALS / name).exists():              # its uncropped original goes with it
            (ORIGINALS / name).replace(REMOVED / f"{dst.stem}_original.jpg")
            moved.append(str(REMOVED / f"{dst.stem}_original.jpg"))
        return {"deleted": name, "primary": im["primary"], "new_files": moved}   # dropped again if validation fails
    return {"deleted": name, "primary": im["primary"]}

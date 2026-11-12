"""Passo 1.3e - Scarica 3-5 immagini con licenza libera per alimento in assets/images/<id>_NN.jpg.

Fonti e licenze ammesse:
- Wikimedia Commons (PD, CC0, CC BY, CC BY-SA): candidati della bozza utente + ricerca per nome scientifico
- Unsplash (Unsplash License; API: attribuzione autore + chiamata a download_location come da linee guida)
- Pixabay (Pixabay Content License)
- iNaturalist (solo foto CC0 / CC BY / CC BY-SA, osservazioni "research grade") -> vista "plant_in_field"
Le immagini vengono ridimensionate (lato lungo max 1600 px), salvate in JPEG q85 senza metadati EXIF; autore,
licenza e URL sorgente in assets/images/_metadata.json. Il tipo di vista è assegnato in base alla query
(da verificare visivamente; eliminare le foto non adatte e lanciare sync_images.py).

Ripresa automatica: data/raw/images_log.json registra cosa è già stato fatto.
Uso:  python scripts/download_images.py [--max-per-item 4] [--unsplash-budget 45] [--only id1,id2]
Nota: l'API Unsplash in modalità demo consente 50 richieste/ora: lo script si ferma col budget indicato e
alla riesecuzione riprende dagli alimenti mancanti.
"""
import io
import re
import sys
import time
import urllib.parse

from PIL import Image

from common import DATA, IMAGES, RAW, SESSION, env, load_json, save_json

LOG = RAW / "images_log.json"
META = IMAGES / "_metadata.json"
OK_LIC = re.compile(r"^(cc0|public domain|pd|cc[- ]by(-sa)?[- ]?\d(\.\d)?|cc by(-sa)? \d\.\d|cc-by-sa-\d\.\d|cc-by-\d\.\d)", re.I)
UNSPLASH = env("UNSPLASH_ACCESS_KEY")
PIXABAY = env("PIXABAY_API_KEY")
UTM = "utm_source=peak_season&utm_medium=referral"


def arg(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def save_image(content, iid, n):
    im = Image.open(io.BytesIO(content))
    if im.mode in ("RGBA", "LA", "P"):                 # PNG con trasparenza -> sfondo bianco
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[3])
        im = bg
    im = im.convert("RGB")
    im.thumbnail((1600, 1600), Image.LANCZOS)
    fn = f"{iid}_{n:02d}.jpg"
    im.save(IMAGES / fn, "JPEG", quality=85, optimize=True, progressive=True)
    return fn, im.size


def get_bytes(url):
    r = SESSION.get(url, timeout=90)
    r.raise_for_status()
    return r.content


# ------------------------------------------------------------------ fonti
def commons_info(titles):
    r = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "titles": "|".join(titles), "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime",
        "iiurlwidth": 1600, "format": "json"}, timeout=60).json()
    out = []
    for p in r.get("query", {}).get("pages", {}).values():
        if "imageinfo" not in p:
            continue
        ii = p["imageinfo"][0]
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName", {}).get("value") or "").strip()
        if not OK_LIC.match(lic) or ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value") or "").strip() or "Wikimedia Commons contributor"
        out.append({"title": p["title"], "url": ii.get("thumburl") or ii["url"], "w": ii.get("width"), "h": ii.get("height"),
                    "author": artist[:120], "license": lic, "license_url": md.get("LicenseUrl", {}).get("value"),
                    "source_url": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                    "provider": "wikimedia_commons"})
    return out


def commons_search(q, limit=6):
    r = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "list": "search", "srsearch": f"{q} filetype:bitmap", "srnamespace": 6, "srlimit": limit,
        "format": "json"}, timeout=60).json()
    titles = [x["title"] for x in r.get("query", {}).get("search", [])]
    return [x for x in commons_info(titles) if (x["w"] or 0) >= 1200] if titles else []


def unsplash(q):
    if not UNSPLASH:
        return []
    r = SESSION.get("https://api.unsplash.com/search/photos", params={"query": q, "per_page": 5, "orientation": "landscape",
                    "content_filter": "high"}, headers={"Authorization": f"Client-ID {UNSPLASH}", "Accept-Version": "v1"}, timeout=60)
    if r.status_code == 403:
        raise RuntimeError("Unsplash rate limit")
    out = []
    for p in r.json().get("results", []):
        out.append({"url": p["urls"]["regular"], "w": p["width"], "h": p["height"],
                    "author": f"{p['user']['name']} / Unsplash", "license": "Unsplash License",
                    "license_url": "https://unsplash.com/license", "source_url": p["links"]["html"] + "?" + UTM,
                    "provider": "unsplash", "download_location": p["links"]["download_location"], "desc": (p.get("alt_description") or "")})
    return out


def unsplash_track(p):
    SESSION.get(p["download_location"], headers={"Authorization": f"Client-ID {UNSPLASH}"}, timeout=30)


def pixabay(q, category, must):
    """must = nome dell'alimento che deve comparire tra i primi 2 tag della foto (evita risultati fuori tema)."""
    if not PIXABAY:
        return []
    r = SESSION.get("https://pixabay.com/api/", params={"key": PIXABAY, "q": q, "image_type": "photo", "category": category,
                    "safesearch": "true", "per_page": 20, "min_width": 1200, "lang": "en"}, timeout=60).json()
    out = []
    for h in r.get("hits", []):
        tags = [t.strip().lower() for t in h.get("tags", "").split(",")][:2]
        if not any(must.lower() in t or t in must.lower() for t in tags):
            continue
        out.append({"url": h["largeImageURL"], "w": h["imageWidth"], "h": h["imageHeight"], "author": f"{h['user']} / Pixabay",
                    "license": "Pixabay Content License", "license_url": "https://pixabay.com/service/license-summary/",
                    "source_url": h["pageURL"], "provider": "pixabay"})
    return out


def inaturalist(sci):
    r = SESSION.get("https://api.inaturalist.org/v1/observations", params={
        "taxon_name": sci, "photo_license": "cc0,cc-by,cc-by-sa", "quality_grade": "research", "per_page": 5,
        "order_by": "votes", "photos": "true"}, timeout=60).json()
    out = []
    for o in r.get("results", []):
        for ph in o.get("photos", [])[:1]:
            lic = (ph.get("license_code") or "").lower()
            if lic not in ("cc0", "cc-by", "cc-by-sa"):
                continue
            out.append({"url": ph["url"].replace("square", "large"), "w": None, "h": None,
                        "author": (ph.get("attribution") or "iNaturalist user")[:140], "license": lic.upper(),
                        "license_url": {"cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
                                        "cc-by": "https://creativecommons.org/licenses/by/4.0/",
                                        "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/"}[lic],
                        "source_url": f"https://www.inaturalist.org/observations/{o['id']}", "provider": "inaturalist"})
    return out


# ------------------------------------------------------------------ main
def main():
    max_per = int(arg("--max-per-item", 4))
    budget = int(arg("--unsplash-budget", 45))
    only = set(arg("--only", "").split(",")) - {""}
    IMAGES.mkdir(parents=True, exist_ok=True)
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")["items"]
    meta = load_json(META) if META.exists() else {}
    log = load_json(LOG) if LOG.exists() else {}
    used_urls = {m["source_url"] for m in meta.values()}
    unsplash_calls = 0
    for it in db["items"]:
        iid = it["id"]
        if only and iid not in only:
            continue
        st = log.setdefault(iid, {"done": [], "errors": []})
        have = sorted(k for k in meta if k.startswith(iid + "_") and (IMAGES / k).exists())
        if len(have) >= max_per or "complete" in st["done"]:
            continue
        en, sci, cat = it["names"]["en"].split("(")[0].strip(), it["botany"]["scientific_name"].split("/")[0].strip(), it["category"]
        kind = {"frutta": "fruit", "verdura": "vegetable", "erbe_spezie": "herb", "funghi": "mushroom", "cereali": "grain"}[cat]
        plan = []   # (fonte, funzione, vista)
        if "unsplash" not in st["done"]:
            plan.append(("unsplash", lambda: unsplash(f"{en} {kind}"), "whole_raw"))
        if "pixabay" not in st["done"]:
            plan.append(("pixabay", lambda: pixabay(f"{en} {kind}", "food", en.split()[0] if len(en.split()[0]) > 3 else en), "whole_raw"))
        if "commons" not in st["done"]:
            def commons_cands(iid=iid, sci=sci):
                titles = [re.sub(r"^.*/wiki/", "", d["source_url"]).replace("_", " ") for d in legacy.get(iid, {}).get("images.image_details", [])]
                c = commons_info([urllib.parse.unquote(t) for t in titles]) if titles else []
                return c or commons_search(sci)
            plan.append(("commons", commons_cands, "whole_raw"))
        if "inaturalist" not in st["done"] and cat not in ("cereali",):
            plan.append(("inaturalist", lambda: inaturalist(sci), "plant_in_field"))
        n = max([int(k[-6:-4]) for k in have] or [0])
        for src, fn, view in plan:
            if len([k for k in meta if k.startswith(iid + "_") and (IMAGES / k).exists()]) >= max_per:
                break
            if src == "unsplash":
                if unsplash_calls >= budget:
                    continue
                unsplash_calls += 1
            try:
                cands = [c for c in fn() if c["source_url"] not in used_urls]
            except Exception as e:  # noqa: BLE001
                st["errors"].append(f"{src}: {str(e)[:120]}")
                if "rate limit" in str(e).lower():
                    budget = 0
                continue
            if src == "commons":
                take = cands[:2]
                # se il candidato della bozza era una sezione, mantieni la vista indicata dalla bozza
                views = {d["source_url"].split("/wiki/")[-1].replace("_", " "): d.get("view_type")
                         for d in legacy.get(iid, {}).get("images.image_details", [])}
            else:
                take = cands[:1]
                views = {}
            for c in take:
                try:
                    content = get_bytes(c["url"])
                    if src == "unsplash":
                        unsplash_track(c); unsplash_calls += 1
                    n += 1
                    fname, size = save_image(content, iid, n)
                    v = views.get(urllib.parse.unquote(c["source_url"].split("/wiki/")[-1]).replace("_", " "), view) or view
                    meta[fname] = {"filename": fname, "author": c["author"], "license": c["license"], "license_url": c.get("license_url"),
                                   "source_url": c["source_url"], "provider": c["provider"], "width": size[0], "height": size[1],
                                   "view_type": v if v in ("whole_raw", "cut_section", "plant_in_field") else view}
                    used_urls.add(c["source_url"])
                except Exception as e:  # noqa: BLE001
                    st["errors"].append(f"{src} download: {str(e)[:120]}")
            st["done"].append(src)
            time.sleep(0.3)
        # rinforzo: se ci sono meno di 3 foto, seconda ricerca su Commons per nome inglese
        if "commons2" not in st["done"] and len([k for k in meta if k.startswith(iid + "_") and (IMAGES / k).exists()]) < 3:
            try:
                for c in [c for c in commons_search(f"{en} {kind}", 10) if c["source_url"] not in used_urls][:3 - len(
                        [k for k in meta if k.startswith(iid + "_") and (IMAGES / k).exists()])]:
                    n += 1
                    fname, size = save_image(get_bytes(c["url"]), iid, n)
                    meta[fname] = {"filename": fname, "author": c["author"], "license": c["license"], "license_url": c.get("license_url"),
                                   "source_url": c["source_url"], "provider": c["provider"], "width": size[0], "height": size[1],
                                   "view_type": "whole_raw"}
                    used_urls.add(c["source_url"])
            except Exception as e:  # noqa: BLE001
                st["errors"].append(f"commons2: {str(e)[:120]}")
            st["done"].append("commons2")
        if all(s in st["done"] for s in ("unsplash", "pixabay", "commons")) and ("inaturalist" in st["done"] or cat == "cereali"):
            st["done"].append("complete")
        save_json(META, meta)
        save_json(LOG, log)
        print(f"{iid}: {len([k for k in meta if k.startswith(iid + '_')])} immagini", flush=True)
    print(f"chiamate Unsplash usate: {unsplash_calls}")


if __name__ == "__main__":
    main()

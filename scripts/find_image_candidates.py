"""Cerca immagini candidate per i 5 tipi richiesti dall'utente (2026-11-05) e ne scarica un'anteprima per la revisione.

Tipi (view_type):
  full_frame          il prodotto riempie tutta l'inquadratura (sarà la foto principale)
  isolated_background prodotto su sfondo bianco o colorato uniforme
  plant_in_field      la pianta viva (non solo fiori, non foto sgranate)
  botanical_plate     tavola botanica / illustrazione anatomica (anche verticale)
  cut_section         prodotto tagliato, sezione
Criteri: orizzontale (tranne le tavole), larghezza >= 1000 px, licenza libera con autore, niente piatti/ricette/scritte.
Fonti: Pixabay API (foto), Wikimedia Commons API (foto di qualità e tavole botaniche di pubblico dominio).
Esclusi: le foto già nel database e quelle che l'utente ha eliminato (ricavate dall'istantanea precedente).
Uscita: assets/images/_candidates/<id>/<tipo>_<n>.jpg (anteprime) e assets/images/_candidates/candidates.json.
Uso:  python scripts/find_image_candidates.py [--items id1,id2] [--per-type 4]
"""
import io
import json
import re
import sys
import time
import urllib.parse

from PIL import Image

from common import DATA, IMAGES, SESSION, env, load_json, save_json

OUT = IMAGES / "_candidates"
PIXABAY = env("PIXABAY_API_KEY")
OK_LIC = re.compile(r"^(cc0|public domain|pd|cc[- ]by(-sa)?[- ]?\d(\.\d)?|cc by(-sa)? \d\.\d)", re.I)
BAD = re.compile(r"\b(salad|soup|dish|plate|bowl|recipe|meal|cooked|juice|smoothie|cake|pie|pasta|pizza|dessert|drink|cocktail|"
                 r"jam|sauce|breakfast|lunch|dinner|text|logo|label|sign|price|cartoon|clipart|vector|drawing|3d|render|illustration)\b", re.I)
TYPES = ["full_frame", "isolated_background", "plant_in_field", "botanical_plate", "cut_section"]
TREE = {"frutta"}
PLATE_CATS = ["Köhler's Medizinal-Pflanzen", "Flora von Deutschland, Österreich und der Schweiz (1885)", "Flora Batava",
              "Plantae Selectae", "Curtis's Botanical Magazine"]


def db_path():
    """Database da usare: variabile d'ambiente IMAGES_DB (es. una copia stabile mentre il database è in modifica), altrimenti data/database.json."""
    import os
    from pathlib import Path
    return Path(os.environ["IMAGES_DB"]) if os.environ.get("IMAGES_DB") else DATA / "database.json"


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def name_re(en):
    """Il nome inglese intero (singolare o plurale) deve comparire in uno dei primi 3 tag. en può essere una lista di nomi."""
    alts = en if isinstance(en, list) else [en]
    bases = [re.escape(re.sub(r"(es|s)$", "", a.lower().strip())) for a in alts]
    return re.compile(r"\b(" + "|".join(bases) + r")(e?s)?\b")


def alt_names():
    from common import CONFIG
    p = CONFIG / "image_search_names.json"
    return {k: v for k, v in load_json(p).items() if not k.startswith("_")} if p.exists() else {}


def uniform_border(path):
    """True se il bordo dell'anteprima è di colore uniforme (sfondo bianco o colorato)."""
    from PIL import ImageStat
    im = Image.open(path).convert("RGB")
    w, h = im.size
    b = max(4, int(min(w, h) * 0.04))
    strips = [im.crop((0, 0, w, b)), im.crop((0, h - b, w, h)), im.crop((0, 0, b, h)), im.crop((w - b, 0, w, h))]
    st = [ImageStat.Stat(x) for x in strips]
    means = [x.mean for x in st]
    spread = max(max(m[c] for m in means) - min(m[c] for m in means) for c in range(3))
    return max(sum(x.stddev) / 3 for x in st) < 14 and spread < 25


def pixabay(q, en, category, orientation="horizontal"):  # en: nome o lista di nomi accettati nei tag
    time.sleep(float(arg("--px-pause", 0.8)))   # limite API: 100 richieste/minuto in totale
    r = SESSION.get("https://pixabay.com/api/", params={"key": PIXABAY, "q": q, "image_type": "photo", "category": category,
                    "orientation": orientation, "safesearch": "true", "per_page": 30, "min_width": 1000, "lang": "en",
                    "order": "popular"}, timeout=60)
    if r.status_code != 200:
        return []
    out = []
    for h in r.json().get("hits", []):
        tags = [t.strip().lower() for t in h.get("tags", "").split(",")]
        if not any(name_re(en).search(t) for t in tags[:3]) or BAD.search(" ".join(tags)):
            continue
        out.append({"provider": "pixabay", "preview": h["webformatURL"], "full": h["largeImageURL"], "w": h["imageWidth"], "h": h["imageHeight"],
                    "author": f"{h['user']} / Pixabay", "license": "Pixabay Content License",
                    "license_url": "https://pixabay.com/service/license-summary/", "source_url": h["pageURL"],
                    "title": ", ".join(tags), "score": h.get("likes", 0) + h.get("downloads", 0) / 100})
    return out


def commons(q, min_w=1000, landscape=True, limit=25):
    r = {}
    for attempt in range(4):
        time.sleep(1.0 + attempt * 5)
        resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "generator": "search", "gsrsearch": f"{q} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": limit,
            "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 640, "format": "json"}, timeout=60)
        if resp.status_code == 200 and resp.text.startswith("{"):
            r = resp.json()
            break
    out = []
    for p in sorted(r.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName", {}).get("value") or "").strip()
        w, h = ii.get("width") or 0, ii.get("height") or 0
        if not OK_LIC.match(lic) or ii.get("mime") not in ("image/jpeg", "image/png") or w < min_w or (landscape and w <= h):
            continue
        desc = re.sub(r"<[^>]+>", " ", (md.get("ImageDescription", {}).get("value") or ""))
        if BAD.search(p["title"]) and "illustration" not in q:
            continue
        artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value") or "").strip() or "Wikimedia Commons contributor"
        full = ii["url"]
        if w > 1600:
            full = ii["thumburl"].replace("/640px-", "/1600px-")
        out.append({"provider": "wikimedia_commons", "preview": ii.get("thumburl") or ii["url"], "full": full, "w": w, "h": h,
                    "author": artist[:120], "license": lic, "license_url": md.get("LicenseUrl", {}).get("value"),
                    "source_url": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                    "title": p["title"][5:] + " " + desc[:120], "score": 0})
    return out


def queries(it, shared, en=None):
    en = en or it["names"]["en"].split("(")[0].strip()
    sci = " ".join(it["botany"]["scientific_name"].split()[:2])
    key = f'"{en}"' if shared else f'"{sci}"'          # specie condivisa da più alimenti (es. Brassica oleracea): nome inglese
    plant = f"{en} tree" if it["category"] in TREE else f"{en} plant"
    plates = [] if shared else [("cmp", f'intitle:Köhler "{sci}"'), ("cmp", f'intitle:Illustration "{sci}"'),
                                ("cmp", f'intitle:"{sci}" Illustration'), ("cmp", f'"{sci}" botanical illustration')]
    return {
        "full_frame": [("px", en, "backgrounds"), ("px", f"{en} pile", "food"), ("px", f"{en} harvest", "food"), ("cm", f'{key} incategory:"Quality images"')],
        "isolated_background": [("px", f"{en} white background", "food"), ("px", f"{en} isolated", "food"), ("cm", f'{key} "white background"')],
        "plant_in_field": [("px", plant, "nature"), ("px", f"{en} garden", "nature"), ("cm", f'{key} plant incategory:"Quality images"')],
        "botanical_plate": plates,
        "cut_section": [("px", f"{en} halved", "food"), ("px", f"{en} sliced", "food"), ("px", f"{en} cut", "food"), ("cm", f'{key} cross section OR halved')],
    }


def preview(url, path):
    try:
        r = SESSION.get(url, timeout=60)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        im.thumbnail((640, 640))
        im.save(path, "JPEG", quality=82)
        return True
    except Exception:
        return False


def merge():
    """Riunisce i file per alimento in assets/images/_candidates/candidates.json."""
    cand = {"_doc": __doc__.split("\n")[0], "items": {}}
    for f in sorted(OUT.glob("*/candidates.json")):
        cand["items"][f.parent.name] = load_json(f)
    if OUT.exists():
        save_json(OUT / "candidates.json", cand)
    return cand


EXTRA = {  # varianti di ricerca usate solo nel secondo passaggio (--fill)
    "full_frame": [("px", "{n} closeup", "food"), ("px", "fresh {n}", "food"), ("px", "{n} market", "food")],
    "isolated_background": [("px", "{n} on white", "food"), ("px", "{n} studio", "food")],
    "plant_in_field": [("px", "{n} field", "nature"), ("px", "{n} crop", "nature"), ("px", "{n} farm", "nature")],
    "botanical_plate": [],
    "cut_section": [("px", "{n} slice", "food"), ("px", "{n} inside", "food")],
}
NO_CUT = {"erbe_spezie", "cereali"}


def fill(db, per, known, rejected):
    """Secondo passaggio: per i tipi con meno di 2 opzioni (candidate + foto attuali valide) cerca altre candidate con i
    nomi alternativi (config/image_search_names.json) e varianti di ricerca, escludendo tutti gli URL già visti
    (compresi quelli scartati al primo passaggio, letti dal backup indicato con --seen-dir). Le nuove candidate sono
    accodate con i numeri successivi e marcate "pass": 2, per la pre-selezione (prune_candidates.py --pass2)."""
    seen_dir = arg("--seen-dir", None)
    alts_all = alt_names()
    only = set(arg("--items", "").split(",")) - {""}
    for it in db["items"]:
        iid = it["id"]
        f = OUT / iid / "candidates.json"
        if not f.exists() or (only and iid not in only):
            continue
        c = load_json(f)
        if c.get("_filled"):
            continue
        seen = set(known | rejected) | {h["source_url"].split("?")[0] for t, l in c.items() if not t.startswith("_") for h in l}
        if seen_dir:
            from pathlib import Path
            bf = Path(seen_dir) / iid / "candidates.json"
            if bf.exists():
                seen |= {h["source_url"].split("?")[0] for t, l in load_json(bf).items() if not t.startswith("_") for h in l}
        have = {}
        for d in it["images"]["image_details"]:
            if not d.get("flags"):
                have[d["view_type"]] = have.get(d["view_type"], 0) + 1
        en = it["names"]["en"].split("(")[0].strip()
        names = [en] + alts_all.get(iid, [])
        sci2 = " ".join(it["botany"]["scientific_name"].split()[:2])
        shared = sum(1 for x in db["items"] if " ".join(x["botany"]["scientific_name"].split()[:2]) == sci2) > 1
        added = {}
        for t in TYPES:
            if t == "cut_section" and it["category"] in NO_CUT:
                continue
            lst = c.setdefault(t, [])
            if len(lst) + have.get(t, 0) >= 2:
                continue
            qs = []
            for nm in names:
                qs += [q for q in queries(it, shared and nm == en, nm)[t] if q not in qs]
                qs += [(k, q.format(n=nm), cat) for k, q, cat in EXTRA[t]]
            want = per - len(lst)
            got = 0
            for kind, q, *cat in qs:
                if got >= want:
                    break
                try:
                    hits = pixabay(q, names, cat[0]) if kind == "px" else commons(q, min_w=800 if kind == "cmp" else 1000, landscape=(kind != "cmp"))
                except Exception as e:
                    print("  errore", iid, t, e)
                    continue
                hits.sort(key=lambda h: -h["score"])
                for h in hits:
                    k = h["source_url"].split("?")[0]
                    if k in seen or got >= want:
                        continue
                    seen.add(k)
                    n = max([int(x["file"].rsplit("_", 1)[1].split(".")[0]) for x in lst] + [0]) + 1
                    fn = f"{t}_{n}.jpg"
                    if not preview(h["preview"], OUT / iid / fn):
                        continue
                    iso_ok = uniform_border(OUT / iid / fn)
                    if (t == "isolated_background") != iso_ok and kind != "cmp":
                        (OUT / iid / fn).unlink()
                        continue
                    if kind == "cmp" and not re.search(re.escape(sci2.split()[0]), h["title"], re.I):
                        (OUT / iid / fn).unlink()
                        continue
                    lst.append({**h, "file": f"{iid}/{fn}", "query": q, "pass": 2})
                    got += 1
            if got:
                added[t] = got
        c["_filled"] = True
        save_json(f, c)
        print(iid, added, flush=True)


def main():
    if "--fill" in sys.argv:
        db = load_json(db_path())
        known = {d["source_url"].split("?")[0] for i in db["items"] for d in i["images"]["image_details"]}
        snap = DATA / "_snapshots" / "_db_before_merge.json"
        rejected = ({d["source_url"].split("?")[0] for i in load_json(snap)["items"] for d in i["images"]["image_details"]} - known) if snap.exists() else set()
        fill(db, int(arg("--per-type", 4)), known, rejected)
        merge()
        return
    if "--merge" in sys.argv:
        print("alimenti con candidate:", len(merge()["items"]))
        return
    db = load_json(db_path())
    only = set(arg("--items", "").split(",")) - {""}
    per = int(arg("--per-type", 4))
    known = {d["source_url"].split("?")[0] for i in db["items"] for d in i["images"]["image_details"]}
    snap = DATA / "_snapshots" / "_db_before_merge.json"
    rejected = set()
    if snap.exists():
        rejected = {d["source_url"].split("?")[0] for i in load_json(snap)["items"] for d in i["images"]["image_details"]} - known
    OUT.mkdir(exist_ok=True)
    cpath = OUT / "candidates.json"
    cand = merge()
    for it in db["items"]:
        iid = it["id"]
        if (only and iid not in only) or (not only and iid in cand["items"]):
            continue
        (OUT / iid).mkdir(exist_ok=True)
        res, seen = {}, set(known | rejected)
        en = it["names"]["en"].split("(")[0].strip()
        sci2 = " ".join(it["botany"]["scientific_name"].split()[:2])
        shared = sum(1 for x in db["items"] if " ".join(x["botany"]["scientific_name"].split()[:2]) == sci2) > 1
        moved, tmp = [], 0
        for f in (OUT / iid).glob("*.jpg"):
            f.unlink()
        alts = alt_names().get(iid, [])
        names = [en] + alts
        allq = {}
        for nm in names:
            for t, qs in queries(it, shared and nm == en, nm).items():
                allq.setdefault(t, []).extend(q for q in qs if q not in allq.get(t, []))
        for t, qs in allq.items():
            got = []
            for kind, q, *cat in qs:
                if len(got) >= per:
                    break
                try:
                    hits = pixabay(q, names, cat[0]) if kind == "px" else commons(q, min_w=800 if kind == "cmp" else 1000, landscape=(kind != "cmp"))
                except Exception as e:
                    print("  errore", iid, t, e)
                    continue
                hits.sort(key=lambda h: -h["score"])
                for h in hits:
                    k = h["source_url"].split("?")[0]
                    if k in seen or len(got) >= per:
                        continue
                    seen.add(k)
                    tmp += 1
                    fn = f"tmp_{tmp}.jpg"
                    if not preview(h["preview"], OUT / iid / fn):
                        continue
                    if kind != "cmp" and t != "isolated_background" and uniform_border(OUT / iid / fn):
                        moved.append((fn, {**h, "query": q}))     # sfondo uniforme: va tra gli isolati
                        continue
                    if t == "isolated_background" and not uniform_border(OUT / iid / fn):
                        (OUT / iid / fn).unlink()
                        continue
                    if kind == "cmp" and not re.search(re.escape(sci2.split()[0]), h["title"], re.I):
                        (OUT / iid / fn).unlink()
                        continue
                    got.append({**h, "file": f"{iid}/{fn}", "query": q})
            res[t] = got
        iso = res.setdefault("isolated_background", [])
        for fn, h in moved:
            if len(iso) >= per + 2:
                (OUT / iid / fn).unlink()
                continue
            iso.append({**h, "file": f"{iid}/{fn}"})
        for t, lst in res.items():                      # nomi definitivi <tipo>_<n>.jpg
            for n, h in enumerate(lst, 1):
                src, dst = OUT / h["file"], OUT / iid / f"{t}_{n}.jpg"
                src.replace(dst)
                h["file"] = f"{iid}/{t}_{n}.jpg"
        cand["items"][iid] = res
        save_json(OUT / iid / "candidates.json", res)     # un file per alimento: più processi in parallelo
        print(iid, {t: len(v) for t, v in res.items()}, flush=True)


if __name__ == "__main__":
    main()

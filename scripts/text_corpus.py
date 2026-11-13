"""Text corpus per product, from the sources already downloaded (for text checks: varieties, parts used, compounds).
Each entry: (source_key, url, text). Used by verify_varieties.py and similar scripts.
"""
import json
import re
import unicodedata

from common import RAW, load_json
from fetch_text_pages import path_for, urls_of

_ALTRO = {}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("'", " ").replace("’", " ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def altroconsumo(it):
    url = next((u for u in it["sources_by_topic"]["seasonality_and_storage_urls"] if "altroconsumo" in u), None)
    if not url:
        return None
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    p = RAW / "altroconsumo" / f"{slug}.json"
    if not p.exists():
        return None
    d = load_json(p)
    return ("altroconsumo", url, (d.get("description") or "") + "\n" + json.dumps(d.get("info", {}), ensure_ascii=False))


def corpus(it, hb66_chapters=None, ucd=None):
    out = []
    for u in urls_of(it, ["ortodacoltivare.it", "my-personaltrainer.it"]):
        p = path_for(u)
        if p.exists():
            out.append(("orto_da_coltivare" if "ortodacoltivare" in u else "my_personaltrainer", u, p.read_text(encoding="utf-8")))
    a = altroconsumo(it)
    if a:
        out.append(a)
    if ucd and it["id"] in ucd:
        out.append(("uc_davis", ucd[it["id"]].get("url"), json.dumps(ucd[it["id"]], ensure_ascii=False)))
    if hb66_chapters:
        for title, txt in hb66_chapters:
            out.append(("usda_hb66", "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf", txt))
    return out

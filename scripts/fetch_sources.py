"""Step 1.1 - Downloads and caches (data/raw/) the master lists of the sources.

Usage:  python scripts/fetch_sources.py [--force]

Produces:
  data/raw/crea_list.json          product name -> CREA code (832 entries)
  data/raw/bda_codes.json          product name -> BDA-IEO code (~1100 entries)
  data/raw/eufic_fvlist.json       raw EUFIC map data {Fruit|Vegetable: {name: [[month, country], ...]}}
  data/raw/altroconsumo_items.json name -> Altroconsumo sheet URL
  data/raw/greenpeace_months.json  "category:name" -> months (from the local PDF)
  data/raw/sitemap_odc.json        Orto da Coltivare sheet URLs (vegetables, fruit, herbs, guides)
  data/raw/sitemap_mypt.json       My-PersonalTrainer URLs
"""
import collections
import html
import json
import re
import sys

from common import FONTI, RAW, http_get, save_json

FORCE = "--force" in sys.argv


def need(name):
    return FORCE or not (RAW / name).exists()


def crea():
    h = http_get("https://www.alimentinutrizione.it/tabelle-nutrizionali/ricerca-per-alimento").text
    pairs = re.findall(r'href="/tabelle-nutrizionali/(\d+)"[^>]*>(.*?)</a>', h, re.S)
    out = {html.unescape(re.sub("<.*?>", "", n)).strip(): c for c, n in pairs}
    save_json(RAW / "crea_list.json", out)
    print("CREA", len(out))


def bda():
    h = http_get("https://bda.ieo.it/?page_id=1161").text
    rows = re.findall(r"<tr[^>]*>\s*<td>(\d+)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>", h, re.S)
    out = {}
    for c, it, en, sci in rows:
        out[html.unescape(it).strip()] = {"code": c, "en": html.unescape(en).strip(),
                                          "sci": html.unescape(sci).replace("\xa0", " ").strip()}
    save_json(RAW / "bda_codes.json", out)
    print("BDA", len(out))


def eufic():
    t = http_get("https://www.eufic.org/en/global/ajax-map").text
    fv = json.loads(t[t.index("{"): t.rindex("}") + 1])
    save_json(RAW / "eufic_fvlist.json", {"_source": "https://www.eufic.org/en/global/ajax-map", **fv})
    print("EUFIC", {k: len(v) for k, v in fv.items()})


def altroconsumo():
    base = "https://www.altroconsumo.it/alimentazione/fare-la-spesa/consigli/calendario-frutta-verdura"
    h = http_get(base).text
    cards = re.findall(r'href="(/alimentazione/fare-la-spesa/consigli/calendario-frutta-verdura/[^"]+)".*?<h3[^>]*>(.*?)</h3>', h, re.S)
    out = {html.unescape(n).strip(): "https://www.altroconsumo.it" + u for u, n in cards}
    save_json(RAW / "altroconsumo_items.json", out)
    print("Altroconsumo", len(out))


def greenpeace():
    from pypdf import PdfReader
    months = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO",
              "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
    r = PdfReader(str(FONTI / "calendario-frutta-e-verdura-di-stagione_greenpeace.pdf"))
    gp = collections.defaultdict(set)
    for pg in r.pages:
        page = pg.extract_text() or ""
        if "CALENDARIO" not in page:
            continue
        m = next((x for x in months if f"\n{x}\n" in page), None)
        if not m:
            continue
        cur, prev = None, ""
        for line in page.split(f"\n{m}\n", 1)[1].splitlines():
            s = line.strip()
            if s.startswith("Frutta"):
                cur = "frutta"; continue
            if s.startswith("Verdura"):
                cur = "verdura"; continue
            if s.startswith("Attenzione"):                 # text box at the end of the page
                cur = None
                continue
            if not s or not cur:
                continue
            if (line.startswith(" ") or s[0].islower()) and prev and len(s.split()) == 1:
                # line wrapped in the PDF, e.g. "Cavolo" / "   cappuccio"
                gp[(cur, prev)].discard(m)
                prev = prev + " " + s
                gp[(cur, prev)].add(m)
                continue
            if s[0].islower():
                continue
            prev = s
            gp[(cur, s)].add(m)
    out = {f"{c}:{n}": sorted(v, key=months.index) for (c, n), v in gp.items() if v}
    save_json(RAW / "greenpeace_months.json", out)
    print("Greenpeace", len(out))


def sitemaps():
    out = []
    for s in ["ortaggio", "frutto", "erba", "guida"]:
        t = http_get(f"https://www.ortodacoltivare.it/{s}-sitemap.xml").text
        out += [u for u in re.findall(r"<loc>(.*?)</loc>", t) if not u.endswith((".jpg", ".png", ".webp"))]
    save_json(RAW / "sitemap_odc.json", out)
    print("Sitemap ODC", len(out))
    t = http_get("https://www.my-personaltrainer.it/sitemap.xml", timeout=120).text
    urls = re.findall(r"<loc>(.*?)</loc>", t)
    save_json(RAW / "sitemap_mypt.json", urls)
    print("Sitemap MyPT", len(urls))


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for fname, fn in [("crea_list.json", crea), ("bda_codes.json", bda), ("eufic_fvlist.json", eufic),
                      ("altroconsumo_items.json", altroconsumo), ("greenpeace_months.json", greenpeace),
                      ("sitemap_mypt.json", sitemaps)]:
        if need(fname):
            fn()
        else:
            print("cache present:", fname)

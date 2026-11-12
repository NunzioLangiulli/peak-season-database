"""Prepara le schede dei fatti per la riscrittura dei testi (data/raw/text_facts.json).

Per ogni alimento raccoglie, in forma compatta, i fatti dalle fonti: Altroconsumo (benefici, scelta, conservazione,
descrizione), Greenpeace (lo sapevi / anti-spreco, 12 alimenti), My-PersonalTrainer (descrizione della scheda),
USDA HB66 (qualità, conservazione, danni da freddo), UC Davis (etilene, freddo), valori verificati del database
(temperatura, UR, durata, etilene, claim, nutrienti >=15% VNR) e i testi della bozza utente.
Uso:  python scripts/build_text_facts.py [--block N --size 12]   (stampa le schede del blocco)
"""
import html
import re
import sys

from common import DATA, FONTI, RAW, http_get, load_json, save_json


def greenpeace_tips():
    from pypdf import PdfReader
    out = {}
    for pg in PdfReader(str(FONTI / "calendario-frutta-e-verdura-di-stagione_greenpeace.pdf")).pages:
        t = pg.extract_text() or ""
        m = re.search(r"(FRUTTO|VERDURA) DEL MESE\s*\n(.+?)\n", t)
        if m:
            name = m.group(2).strip().title()
            sap = re.search(r"LO SAPEVI CHE…\?(.*?)(CONSIGLI ANTI-SPRECO|$)", t, re.S)
            anti = re.search(r"CONSIGLI ANTI-SPRECO(.*?)(GENNAIO|FEBBRAIO|MARZO|APRILE|MAGGIO|GIUGNO|LUGLIO|AGOSTO|SETTEMBRE|OTTOBRE|NOVEMBRE|DICEMBRE|$)", t, re.S)
            clean = lambda s: re.sub(r"\s+", " ", s).strip() if s else None  # noqa: E731
            out[name] = {"lo_sapevi": clean(sap.group(1)) if sap else None, "anti_spreco": clean(anti.group(1)) if anti else None}
    return out


def mypt_desc(url):
    p = RAW / "mypt_desc.json"
    cache = load_json(p) if p.exists() else {}
    if url not in cache:
        try:
            h = http_get(url, timeout=40).text
            m = re.search(r'<meta name="description" content="([^"]*)"', h)
            cache[url] = html.unescape(m.group(1)) if m else None
        except Exception:  # noqa: BLE001
            cache[url] = None
        save_json(p, cache)
    return cache[url]


def hb66_snippets(iid):
    import enrich_postharvest as ep
    title = ep.MAP.get(iid, (None,))[0]
    if not title:
        return {}
    chap, _ = CHAP
    ch = next((v for k, v in chap.items() if k.startswith(title)), None)
    if not ch:
        return {}
    g = lambda n, k=320: (ep.section(ch["text"], n) or "")[:k] or None  # noqa: E731
    return {"quality": g("Quality Characteristics and Criteria"), "storage": g("Optimum Storage Conditions") or g("Storage Conditions"),
            "chilling": g("Chilling Sensitivity", 260), "ethylene": g("Ethylene Production and Sensitivity", 220),
            "climacteric_word": ("nonclimacteric" if re.search(r"non-?climacteric", ch["text"], re.I) else
                                 "climacteric" if re.search(r"\bclimacteric\b", ch["text"], re.I) else None)}


CHAP = None


def main():
    global CHAP
    import enrich_postharvest as ep
    CHAP = ep.load_hb66()
    db = load_json(DATA / "database.json")
    idx = {i["id"]: i for i in load_json(DATA / "items_index.json")["items"]}
    ucd = load_json(RAW / "ucdavis_extract.json")["sheets"]
    gp = greenpeace_tips()
    facts = {}
    for it in db["items"]:
        iid, s = it["id"], idx[it["id"]]["sources"]
        n, r = it["nutrition_and_sustainability"], it["ripening_and_storage"]
        ph, e = r["postharvest_physiology"], r["ethylene_compatibility"]
        altro = None
        if s.get("altroconsumo_url"):
            p = RAW / "altroconsumo" / (s["altroconsumo_url"].rstrip("/").rsplit("/", 1)[-1] + ".json")
            altro = load_json(p) if p.exists() else None
        u = ucd.get((s.get("uc_davis") or {}).get("slug")) or {}
        gpk = next((k for k in gp if s.get("greenpeace_name") and k.lower().startswith(s["greenpeace_name"].lower()[:5])), None)
        facts[iid] = {
            "nome": f"{it['names']['it']} / {it['names']['en']} ({it['botany']['scientific_name']}), {it['category']}",
            "valori": {"T": ph["optimal_temperature_c"], "UR": ph["optimal_humidity_percent"], "frigo_gg": ph["estimated_shelf_life_days"]["refrigerated_days"],
                       "freddo": [ph["chilling_injury"]["susceptible"], ph["chilling_injury"]["critical_temperature_c"]],
                       "etilene": [e["ethylene_production_class"], "sensibile" if e["sensitive_to_ethylene"] else "non sens." if e["sensitive_to_ethylene"] is False else "?"],
                       "claim": (n["nutrition_claims_eu"] or {}).get("it"),
                       "nutrienti_15": [f"{x['name']} {x['percent_nrv']}%" for x in n["vitamins"] + n["minerals"] if (x.get("percent_nrv") or 0) >= 15],
                       "kcal": n["kcal_per_100g"]},
            "altroconsumo": (altro or {}).get("info"),
            "altro_desc": (altro or {}).get("description"),
            "greenpeace": gp.get(gpk) if gpk else None,
            "mypt": mypt_desc(s["my_personaltrainer_url"]) if s.get("my_personaltrainer_url") else None,
            "hb66": hb66_snippets(iid),
            "ucdavis": {"eth": u.get("ER"), "freddo": u.get("CI")} if u else None,
            "bozza": {k: (v or {}).get("it") if isinstance(v, dict) else v for k, v in {
                "spesa": it["buying_guide"]["shopping_list_preview"], "scelta": it["buying_guide"]["detailed_selection"],
                "conserv": r["storage_instructions"], "benefici": n["health_benefits_and_curiosities"],
                "spreco": n["culinary_waste_reduction"], "luogo": r["primary_location"], "maturaz": r["ripening_type"]}.items()},
        }
    save_json(RAW / "text_facts.json", facts)
    print("schede fatti:", len(facts))


def show(block, size):
    facts = load_json(RAW / "text_facts.json")
    ids = list(facts)[(block - 1) * size: block * size]
    cut = lambda s, n: (s[:n] + "…") if isinstance(s, str) and len(s) > n else s  # noqa: E731
    for i in ids:
        f = facts[i]
        v = f["valori"]
        print(f"### {i} | {f['nome']}")
        print(f"- V: T{v['T'] and (v['T']['min'], v['T']['max'])} UR{v['UR'] and (v['UR']['min'], v['UR']['max'])} frigo{v['frigo_gg']} "
              f"freddo{v['freddo']} et{v['etilene']} | nutr15: {', '.join(v['nutrienti_15'])}")
        if f.get("altroconsumo"):
            print("- AC:", " | ".join(f"{k}: {cut(x, 140)}" for k, x in f["altroconsumo"].items() if x))
        if f.get("altro_desc"):
            print("- ACd:", cut(f["altro_desc"], 200))
        if f.get("greenpeace"):
            print("- GP:", " | ".join(f"{k}: {cut(x, 260)}" for k, x in f["greenpeace"].items() if x))
        h = f.get("hb66") or {}
        for k in ("quality", "storage", "chilling"):
            if h.get(k):
                print(f"- HB {k}: {cut(h[k], 200)}")
        if h.get("climacteric_word"):
            print("- HB clim:", h["climacteric_word"])
        b = f.get("bozza") or {}
        print(f"- BZ luogo={b.get('luogo')} mat={b.get('maturaz')} | spesa: {cut(b.get('spesa'), 120)} | benefici: {cut(b.get('benefici'), 180)} | spreco: {cut(b.get('spreco'), 160)}")


if __name__ == "__main__":
    if "--block" in sys.argv:
        show(int(sys.argv[sys.argv.index("--block") + 1]), int(sys.argv[sys.argv.index("--size") + 1]) if "--size" in sys.argv else 12)
    else:
        main()

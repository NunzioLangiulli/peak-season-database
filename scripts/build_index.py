"""Step 1.1 - Generates data/items_index.json (master index of the products).

Merges the 91 products of the owner's draft (data/_backup_bozza_2026-11-04/database.json, not published) with the new
products selected in scripts/config/catalog.json and, for each one, checks and records the REAL
entries of every source (CREA/BDA-IEO codes, UC Davis sheets, ODC/WWF/Greenpeace/BioSuisse rows,
EUFIC keys, Altroconsumo/ODC/My-PersonalTrainer sheets, EPPO code, WFO ID).

Usage:  python scripts/fetch_sources.py   (once, fills data/raw/)
      python scripts/build_index.py
"""
import collections
import datetime
import re
import urllib.parse

from common import CONFIG, DATA, RAW, curl_get_json, cached_json, env, http_get, load_json, save_json

DRAFT = DATA / "_backup_bozza_2026-11-04" / "database.json"
CATEGORIES = ["verdura", "frutta", "erbe_spezie", "funghi", "cereali"]
ODC_SECTIONS = ("/ortaggi/", "/alberi-da-frutto/", "/coltivare-frutti-di-bosco/", "/erbe-aromatiche/",
                "/frutti-di-bosco/", "/piante-aromatiche/", "/erbe/", "/frutti/")


def binomial(sci):
    """'Cynara cardunculus var. scolymus' -> ['Cynara cardunculus var. scolymus', 'Cynara cardunculus']"""
    sci = sci.split("/")[0].strip()
    sci = re.sub(r"\s+", " ", sci)
    parts = sci.replace("× ", "x ").split(" ")
    tries = [sci]
    if len(parts) > 2:
        tries.append(" ".join(parts[:2]) if parts[1] not in ("x", "×") else " ".join(parts[:3]))
    return list(dict.fromkeys(tries))


# ------------------------------------------------------------------ EPPO / WFO / GBIF
EPPO_KEY = env("EPPO_API_KEY")


def eppo_names(code):
    hdr = {"X-Api-Key": EPPO_KEY}

    def fetch_names():
        r = http_get(f"https://api.eppo.int/gd/v2/taxons/taxon/{code}/names", headers=hdr)
        return r.json() if r.ok else {"http": r.status_code}
    return cached_json(RAW / "eppo_cache.json", "names|" + code, fetch_names)


def eppo_lookup(sci, override=None):
    """EPPO name2codes accepts only the exact preferred name. If the catalogue gives a code
    (override), the code is VERIFIED by reading the names from the API: if it does not exist -> not_found."""
    if not EPPO_KEY:
        return {"status": "no_api_key"}
    hdr = {"X-Api-Key": EPPO_KEY}
    if override:
        names = eppo_names(override)
        if isinstance(names, list) and names:
            pref = next((n["fullname"] for n in names if n.get("lang_iso") == "la" and n.get("preferred")), None)
            return {"status": "ok", "eppo_code": override, "matched_on": "codice verificato via API (catalogo)",
                    "eppo_preferred_name": pref,
                    "common_names": {lang: [n["fullname"] for n in names if n.get("lang_iso") == lang][:6] for lang in ("it", "en")},
                    "url": f"https://gd.eppo.int/taxon/{override}"}
        return {"status": "override_not_found", "eppo_code": override}
    for q in binomial(sci):
        def fetch(q=q):
            r = http_get("https://api.eppo.int/gd/v2/tools/name2codes", params={"name": q}, headers=hdr)
            return r.json() if r.ok else {"http": r.status_code}
        res = cached_json(RAW / "eppo_cache.json", "name2codes|" + q, fetch)
        if isinstance(res, list) and res:
            code = next((x["eppocode"] for x in res if x.get("preferred")), res[0]["eppocode"])
            names = eppo_names(code)
            pref = next((n["fullname"] for n in names if n.get("lang_iso") == "la" and n.get("preferred")), None) if isinstance(names, list) else None
            common = {}
            if isinstance(names, list):
                for lang in ("it", "en"):
                    common[lang] = [n["fullname"] for n in names if n.get("lang_iso") == lang][:6]
            return {"status": "ok", "eppo_code": code, "matched_on": q, "eppo_preferred_name": pref,
                    "common_names": common, "url": f"https://gd.eppo.int/taxon/{code}"}
    return {"status": "not_found", "tried": binomial(sci)}


def wfo_lookup(sci):
    for q in binomial(sci):
        url = "https://list.worldfloraonline.org/matching_rest.php?input_string=" + urllib.parse.quote(q)
        try:
            res = cached_json(RAW / "wfo_cache.json", q, lambda url=url: curl_get_json(url))
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "error": str(e)[:120]}
        cands = res.get("candidates") or []
        # prefer: exact match > accepted name (placement without '$', i.e. not a synonym) > Linnaeus as author
        accepted = [x for x in cands if "$" not in x.get("placement", "") and x.get("placement")]
        linn = [x for x in accepted if re.search(r"\bL\.(\s|$)|\(L\.\)", x.get("full_name_plain", ""))]
        cand = res.get("match") or (linn or accepted or cands or [None])[0]
        if cand:
            placement = cand.get("placement", "")
            fam = next((p for p in placement.split("/") if p.endswith("aceae")), None)
            return {"status": "ok" if res.get("match") else "candidate", "wfo_id": cand["wfo_id"],
                    "name": cand.get("full_name_plain"), "family": fam, "matched_on": q,
                    "url": f"https://www.worldfloraonline.org/taxon/{cand['wfo_id']}"}
    return {"status": "not_found", "tried": binomial(sci)}


def gbif_lookup(sci):
    q = binomial(sci)[0]

    def fetch():
        r = http_get("https://api.gbif.org/v1/species/match", params={"name": q})
        return r.json() if r.ok else {"http": r.status_code}
    res = cached_json(RAW / "gbif_cache.json", q, fetch)
    if res.get("usageKey"):
        return {"status": res.get("matchType", "").lower(), "gbif_key": res["usageKey"], "name": res.get("scientificName"),
                "family": res.get("family"), "url": f"https://www.gbif.org/species/{res['usageKey']}"}
    return {"status": "not_found"}


# ------------------------------------------------------------------ sitemaps
def pick_odc(kws, sitemap):
    best = []
    for u in sitemap:
        if not any(s in u for s in ODC_SECTIONS):
            continue
        slug = u.rstrip("/").rsplit("/", 1)[-1]
        for k in kws:
            k2 = k.replace(" ", "-").replace("'", "-")
            if slug == k2 or slug.startswith(k2):
                best.append((len(slug), u))
    return sorted(best)[0][1] if best else None


def pick_mypt(kws, sitemap):
    cands = []
    for u in sitemap:
        m = re.match(r"https://www\.my-personaltrainer\.it/(alimentazione|Tv/Ricette/Ingredienti)/([^/]+)\.html$", u)
        if not m:
            continue
        sec, slug = m.groups()
        for k in kws:
            k2 = k.replace(" ", "-").replace("'", "-")
            if slug == k2 or (slug.startswith(k2) and len(slug) <= len(k2) + 4):
                cands.append((0 if sec == "alimentazione" else 1, len(slug), u))
    return sorted(cands)[0][2] if cands else None


# ------------------------------------------------------------------ main
def main():
    draft = {it["id"]: it for it in load_json(DRAFT)["items"]}
    cat = load_json(CONFIG / "catalog.json")
    crea = {v: k for k, v in load_json(RAW / "crea_list.json").items()}
    bda = {v["code"]: k for k, v in load_json(RAW / "bda_codes.json").items()}
    eufic = load_json(RAW / "eufic_fvlist.json")
    eufic_keys = {k: c for c in ("Fruit", "Vegetable") for k in eufic[c]}
    ucd = load_json(RAW / "ucdavis_slugs.json")
    altro = load_json(RAW / "altroconsumo_items.json")
    gp = load_json(RAW / "greenpeace_months.json")
    gp_names = {k.split(":", 1)[1] for k in gp}
    pdf = load_json(RAW / "local_pdf_lists.json")
    odc_rows, wwf_rows, bs_rows = (set(pdf[k]["rows"]) for k in ("odc_rows", "wwf", "biosuisse"))
    sm_odc = load_json(RAW / "sitemap_odc.json")
    sm_mypt = load_json(RAW / "sitemap_mypt.json")

    problems = []
    out_items = []
    for c in cat["items"]:
        iid = c["id"]
        d = draft.get(c.get("draft_id", iid))
        if not c.get("new") and not d:
            problems.append(f"{iid}: non presente nella bozza")
            continue
        ov = c.get("override", {})
        names = ov.get("names") or (d["names"] if d else {"it": c["it"], "en": c["en"]})
        category = d["category"] if d else c["cat"]
        sci = ov.get("scientific_name") or (d["botany"]["scientific_name"] if d else c["sci"])
        assert category in CATEGORIES, iid

        def chk(cond, msg):
            if not cond:
                problems.append(f"{iid}: {msg}")
            return cond

        src = collections.OrderedDict()
        # --- composizione
        if c.get("crea"):
            ok = chk(c["crea"] in crea, f"codice CREA {c['crea']} inesistente")
            src["crea"] = {"code": c["crea"], "name": crea.get(c["crea"]), "match": c.get("crea_q", "exact"),
                           "url": f"https://www.alimentinutrizione.it/tabelle-nutrizionali/{c['crea']}" if ok else None}
        else:
            src["crea"] = None
        if c.get("crea_note"):
            src["crea_note"] = c["crea_note"]
        if c.get("bda"):
            ok = chk(c["bda"] in bda, f"codice BDA {c['bda']} inesistente")
            src["bda_ieo"] = {"code": c["bda"], "name": bda.get(c["bda"]), "match": c.get("bda_q", "exact"),
                              "url": "https://bda.ieo.it/?page_id=87",
                              "api": {"endpoint": "https://bda.ieo.it/api/BDA/FoodComponents", "method": "POST",
                                      "body": {"language": 0, "foodId": f"<idFood da SearchFoodByCode '{c['bda']}'>"}}}
        else:
            src["bda_ieo"] = None
        # --- post-raccolta
        if c.get("ucd"):
            chk(c["ucd"] in ucd["slugs"], f"scheda UC Davis {c['ucd']} inesistente")
            src["uc_davis"] = {"slug": c["ucd"], "title": ucd["slugs"].get(c["ucd"]), "match": c.get("ucd_q", "exact"),
                               "url": ucd["base_url"] + c["ucd"]}
        else:
            src["uc_davis"] = None
        src["usda_hb66"] = {"url": "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf",
                            "note": "voce da individuare nel PDF al Passo 1.3"}
        # --- stagionalita / agronomia (fonti locali)
        src["odc_pdf_row"] = c.get("odc_row") if c.get("odc_row") and chk(c["odc_row"] in odc_rows, f"riga ODC '{c['odc_row']}' assente") else None
        src["wwf_row"] = c.get("wwf") if c.get("wwf") and chk(c["wwf"] in wwf_rows, f"riga WWF '{c['wwf']}' assente") else None
        src["greenpeace_name"] = c.get("gp") if c.get("gp") and chk(c["gp"] in gp_names, f"voce Greenpeace '{c['gp']}' assente") else None
        src["biosuisse_row"] = c.get("bs") if c.get("bs") and chk(c["bs"] in bs_rows, f"riga BioSuisse '{c['bs']}' assente") else None
        # --- web
        if c.get("altro"):
            chk(c["altro"] in altro, f"scheda Altroconsumo '{c['altro']}' assente")
        src["altroconsumo_url"] = altro.get(c.get("altro")) if c.get("altro") else None
        # sheet URLs: curated override in the catalogue (checked against the sitemap) or automatic keyword search
        if "odc_url" in c:
            u = "https://www.ortodacoltivare.it" + c["odc_url"] if c["odc_url"] else None
            if u:
                chk(u in sm_odc, f"URL ODC {u} non presente in sitemap")
            src["ortodacoltivare_url"] = u
        else:
            src["ortodacoltivare_url"] = pick_odc(c.get("kw", []), sm_odc)
        if "mypt_url" in c:
            u = "https://www.my-personaltrainer.it" + c["mypt_url"] if c["mypt_url"] else None
            if u:
                chk(u in sm_mypt, f"URL MyPT {u} non presente in sitemap")
            src["my_personaltrainer_url"] = u
        else:
            src["my_personaltrainer_url"] = pick_mypt(c.get("kw", []), sm_mypt)
        ek = [k for k in c.get("eufic", []) if chk(k in eufic_keys, f"chiave EUFIC '{k}' assente")]
        src["eufic_keys"] = ek
        src["eufic_countries"] = sorted({e[1].strip() for k in ek for e in eufic[eufic_keys[k]][k]})
        # --- botanica
        bot = {"scientific_name_draft": sci}
        bot["eppo"] = eppo_lookup(sci, c.get("eppo"))
        if category == "funghi":
            bot["gbif"] = gbif_lookup(sci)
        else:
            bot["wfo"] = wfo_lookup(c.get("wfo_q") or sci)

        seasonal_sources = [k for k in ("odc_pdf_row", "wwf_row", "greenpeace_name", "biosuisse_row", "altroconsumo_url") if src.get(k)]
        if src["eufic_countries"]:
            seasonal_sources.append("eufic")
        out_items.append({
            "id": iid,
            "names": names,
            "scientific_name": sci,
            "category": category,
            "present_in_draft": d is not None,
            "draft_id": d["id"] if d and d["id"] != iid else None,
            "override_reason": ov.get("reason"),
            "added_from_sources": None if d else "criterio: >=2 fonti stagionali/conservazione + scheda di composizione CREA o BDA-IEO",
            "botany_check": bot,
            "sources": src,
            "coverage": {
                "nutrition": bool(src["crea"] or src["bda_ieo"]),
                "postharvest_ucdavis": bool(src["uc_davis"]),
                "agronomy_odc": bool(src["odc_pdf_row"]),
                "seasonality_sources": seasonal_sources,
                "eppo_code": bot["eppo"].get("eppo_code"),
            },
            "completion_status": "indexed",
        })

    # riepilogo
    cats = collections.Counter(i["category"] for i in out_items)
    index = {
        "generated": datetime.date.today().isoformat(),
        "generator": "scripts/build_index.py",
        "total_items": len(out_items),
        "from_draft": sum(i["present_in_draft"] for i in out_items),
        "new_items": sum(not i["present_in_draft"] for i in out_items),
        "categories_breakdown": {k: cats.get(k, 0) for k in CATEGORIES},
        "excluded_candidates": cat.get("excluded_candidates", []),
        "items": out_items,
    }
    save_json(DATA / "items_index.json", index)
    missing_draft = set(draft) - {i["draft_id"] or i["id"] for i in out_items}
    print(f"Index: {len(out_items)} products ({index['from_draft']} draft + {index['new_items']} new) {dict(cats)}")
    if missing_draft:
        print("WARNING draft products not indexed:", sorted(missing_draft))
    print(f"Mapping problems: {len(problems)}")
    for p in problems:
        print("  -", p)


if __name__ == "__main__":
    main()

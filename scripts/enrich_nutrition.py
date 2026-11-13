"""Step 1.3a - Nutrition (CREA 2019 + BDA-IEO) and EU nutrition claims.

- CREA: HTML table of the record (code from the index). Cache: data/raw/crea/<code>.json
- BDA-IEO: API POST /api/BDA/SearchFoodByCode + /api/BDA/FoodComponents. Cache: data/raw/bda/<code>.json
- Primary source = CREA if the match is 'exact', otherwise BDA-IEO 'exact', otherwise whichever is available
  (flagged as an approximation). Nutrients missing from the primary source are filled in from the other.
- %NRV: Reg. (EU) 1169/2011, Annex XIII, part A.
- Claims: Reg. (EC) 1924/2006, Annex (wording of the consolidated IT text of 13.12.2014), thresholds per 100 g of solid.
- Draft values differing from the source (>10% and >0.5 units) -> data_completeness.discrepancies.

Processes blocks of 15 products and saves database.json after each block.
Usage:  python scripts/enrich_nutrition.py
"""
import html
import re

from common import (DATA, RAW, add_discrepancy, finalize_completeness, http_get, http_post_json, iter_blocks,
                    load_json, mark_enriched, save_json)

# --- Reg. (UE) 1169/2011 Allegato XIII parte A: VNR adulti
NRV = {"vit_a": (800, "µg"), "vit_d": (5, "µg"), "vit_e": (12, "mg"), "vit_k": (75, "µg"), "vit_c": (80, "mg"),
       "vit_b1": (1.1, "mg"), "vit_b2": (1.4, "mg"), "niacin": (16, "mg"), "vit_b6": (1.4, "mg"), "folate": (200, "µg"),
       "vit_b12": (2.5, "µg"), "potassium": (2000, "mg"), "calcium": (800, "mg"), "phosphorus": (700, "mg"),
       "magnesium": (375, "mg"), "iron": (14, "mg"), "zinc": (10, "mg"), "copper": (1, "mg"), "manganese": (2, "mg"),
       "selenium": (55, "µg"), "iodine": (150, "µg")}
NAMES = {  # key -> (IT name in the record, EN name, IT name in the claim, EN name in the claim, type)
    "vit_a": ("Vitamina A (retinolo eq.)", "Vitamin A (retinol eq.)", "vitamina A", "vitamin A", "v"),
    "beta_carotene": ("Beta-carotene", "Beta-carotene", None, None, "b"),
    "vit_d": ("Vitamina D", "Vitamin D", "vitamina D", "vitamin D", "v"),
    "vit_e": ("Vitamina E", "Vitamin E", "vitamina E", "vitamin E", "v"),
    "vit_k": ("Vitamina K", "Vitamin K", "vitamina K", "vitamin K", "v"),
    "vit_c": ("Vitamina C", "Vitamin C", "vitamina C", "vitamin C", "v"),
    "vit_b1": ("Tiamina (B1)", "Thiamin (B1)", "tiamina", "thiamin", "v"),
    "vit_b2": ("Riboflavina (B2)", "Riboflavin (B2)", "riboflavina", "riboflavin", "v"),
    "niacin": ("Niacina (B3)", "Niacin (B3)", "niacina", "niacin", "v"),
    "vit_b6": ("Vitamina B6", "Vitamin B6", "vitamina B6", "vitamin B6", "v"),
    "folate": ("Folati (B9)", "Folate (B9)", "folato", "folate", "v"),
    "vit_b12": ("Vitamina B12", "Vitamin B12", "vitamina B12", "vitamin B12", "v"),
    "sodium": ("Sodio", "Sodium", None, None, "m"),
    "potassium": ("Potassio", "Potassium", "potassio", "potassium", "m"),
    "calcium": ("Calcio", "Calcium", "calcio", "calcium", "m"),
    "phosphorus": ("Fosforo", "Phosphorus", "fosforo", "phosphorus", "m"),
    "magnesium": ("Magnesio", "Magnesium", "magnesio", "magnesium", "m"),
    "iron": ("Ferro", "Iron", "ferro", "iron", "m"),
    "zinc": ("Zinco", "Zinc", "zinco", "zinc", "m"),
    "copper": ("Rame", "Copper", "rame", "copper", "m"),
    "manganese": ("Manganese", "Manganese", "manganese", "manganese", "m"),
    "selenium": ("Selenio", "Selenium", "selenio", "selenium", "m"),
    "iodine": ("Iodio", "Iodine", "iodio", "iodine", "m"),
}


def canon(name):
    """Nome nutriente (CREA o BDA) -> chiave canonica, o None."""
    n = name.lower().strip()
    if "animal" in n or "vegetal" in n:
        return None
    rules = [
        (r"^parte edibile", "edible"), (r"^acqua", "water"), (r"^energia.*kcal", "kcal"), (r"^energia.*kj", "kj"),
        (r"^proteine", "protein"), (r"^lipidi", "fat"), (r"^carboidrati disponibili", "carbs"), (r"^amido", "starch"),
        (r"^(zuccheri solubili|carboidrati solubili)", "sugars"), (r"^fibra", "fiber"),
        (r"^sodio", "sodium"), (r"^potassio", "potassium"), (r"^calcio", "calcium"), (r"^magnesio", "magnesium"),
        (r"^fosforo", "phosphorus"), (r"^ferro", "iron"), (r"^rame", "copper"), (r"^zinco", "zinc"),
        (r"^manganese", "manganese"), (r"^selenio", "selenium"), (r"^iodio", "iodine"),
        (r"tiamina|vitamina b1\b", "vit_b1"), (r"riboflavina|vitamina b2\b", "vit_b2"), (r"^niacina", "niacin"),
        (r"vitamina b6", "vit_b6"), (r"folati|folico", "folate"), (r"vitamina b12", "vit_b12"),
        (r"^vitamina c", "vit_c"), (r"retinolo equivalente|vitamina a, retinolo eq", "vit_a"),
        (r"beta-?carotene", "beta_carotene"), (r"^vitamina d", "vit_d"), (r"^vitamina e|tocoferol", "vit_e"),
        (r"^vitamina k", "vit_k"),
    ]
    for pat, key in rules:
        if re.search(pat, n):
            return key
    return None


def num(s):
    s = str(s).strip().replace(",", ".")
    if s.lower() in ("tr", "traccia", "tracce"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def unit_norm(u):
    u = (u or "").strip().replace("μ", "µ").replace("ug", "µg")
    return "g" if u.startswith("g") else u


# ---------------------------------------------------------------- fetch
def fetch_crea(code):
    p = RAW / "crea" / f"{code}.json"
    if p.exists():
        return load_json(p)
    h = http_get(f"https://www.alimentinutrizione.it/tabelle-nutrizionali/{code}").text
    out = {"code": code, "url": f"https://www.alimentinutrizione.it/tabelle-nutrizionali/{code}", "values": {}}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(cells) >= 2 and cells[0].lower().startswith("parte edibile"):
            out["values"]["edible"] = {"v": num(cells[1].replace("%", "")), "u": "%", "raw": cells[0]}
            continue
        if len(cells) >= 3:
            key = canon(cells[0])
            v = num(cells[2])
            if key and v is not None and key not in out["values"]:
                out["values"][key] = {"v": v, "u": unit_norm(cells[1]), "raw": cells[0]}
    m = re.search(r"Nome Scientifico\s*</td>\s*<td[^>]*>(.*?)</td>", h, re.S)
    out["scientific_name"] = html.unescape(re.sub("<.*?>", "", m.group(1))).strip() if m else None
    save_json(p, out)
    return out


def fetch_bda(code):
    """Cache of the raw API response (data/raw/bda/<code>.json), then parsing."""
    p = RAW / "bda" / f"{code}.json"
    if p.exists() and "raw_components" in load_json(p):
        raw = load_json(p)
    else:
        r = http_post_json("https://bda.ieo.it/api/BDA/SearchFoodByCode", {"language": 0, "searchValue": code}).json()
        foods = [f for f in r.get("foods", []) if f.get("idFoodShort") == code]
        raw = {"code": code, "food": foods[0] if foods else None, "raw_components": []}
        if foods:
            comp = http_post_json("https://bda.ieo.it/api/BDA/FoodComponents", {"language": 0, "foodId": foods[0]["idFood"]}).json()
            raw["raw_components"] = comp.get("foodComponents", [])
        save_json(p, raw)
    out = {"code": code, "url": "https://bda.ieo.it/?page_id=87", "values": {},
           "description": (raw["food"] or {}).get("description", "").strip() or None}
    for fam in raw["raw_components"]:
        for c in fam.get("components", []):
            unit = (c.get("cnum") or "").strip()
            name = c.get("dscomp", "")
            key = canon(f"{name}, {unit}") if name.lower().startswith("energia") else canon(name)
            if name.lower().startswith("energia") and "fibra" not in name.lower():
                continue   # uses the "Ric con fibra" energy (consistent with the CREA/Southgate method)
            v = num(c.get("valore", ""))
            if key and v is not None and key not in out["values"]:
                out["values"][key] = {"v": v, "u": unit_norm(unit), "raw": name, "ref": c.get("dsfonte")}
    return out


# ---------------------------------------------------------------- build
def claims(n):
    it, en = [], []
    kcal, fat, sug, fib, prot = (n.get(k) for k in ("kcal", "fat", "sugars", "fiber", "protein"))
    na = n.get("sodium")
    if kcal is not None and kcal <= 40:
        it.append("A basso contenuto calorico"); en.append("Low energy")
    if fat is not None:
        if fat <= 0.5:
            it.append("Senza grassi"); en.append("Fat-free")
        elif fat <= 3:
            it.append("A basso contenuto di grassi"); en.append("Low fat")
    if sug is not None:
        if sug <= 0.5:
            it.append("Senza zuccheri"); en.append("Sugars-free")
        elif sug <= 5:
            it.append("A basso contenuto di zuccheri"); en.append("Low sugars")
    if na is not None:
        g = na / 1000
        if g <= 0.005:
            it.append("Senza sodio o senza sale"); en.append("Sodium-free or salt-free")
        elif g <= 0.04:
            it.append("A bassissimo contenuto di sodio/sale"); en.append("Very low sodium/salt")
        elif g <= 0.12:
            it.append("A basso contenuto di sodio/sale"); en.append("Low sodium/salt")
    if fib is not None:
        per100kcal = fib / kcal * 100 if kcal else 0
        if fib >= 6 or per100kcal >= 3:
            it.append("Ad alto contenuto di fibre"); en.append("High fibre")
        elif fib >= 3 or per100kcal >= 1.5:
            it.append("Fonte di fibre"); en.append("Source of fibre")
    if prot is not None and kcal:
        share = prot * 4 / kcal
        if share >= 0.20:
            it.append("Ad alto contenuto di proteine"); en.append("High protein")
        elif share >= 0.12:
            it.append("Fonte di proteine"); en.append("Source of protein")
    hi_it, hi_en, so_it, so_en = [], [], [], []
    for k, (ref, _u) in NRV.items():
        v = n.get(k)
        if v is None:
            continue
        pct = v / ref * 100
        nm = NAMES[k]
        if pct >= 30:
            hi_it.append(nm[2]); hi_en.append(nm[3])
        elif pct >= 15:
            so_it.append(nm[2]); so_en.append(nm[3])
    it += [f"Ad alto contenuto di {x}" for x in hi_it] + [f"Fonte di {x}" for x in so_it]
    en += [f"High {x}" for x in hi_en] + [f"Source of {x}" for x in so_en]
    return {"it": it, "en": en}


def enrich(item, crea, bda, idx):
    src = idx["sources"]
    c_ok = crea and crea["values"]
    b_ok = bda and bda["values"]
    if not (c_ok or b_ok):
        return False
    c_exact = c_ok and (src.get("crea") or {}).get("match") == "exact"
    b_exact = b_ok and (src.get("bda_ieo") or {}).get("match") == "exact"
    if c_exact or (c_ok and not b_exact):
        prim, prim_name, sec, sec_name = crea, f"CREA {crea['code']}", bda, (f"BDA-IEO {bda['code']}" if b_ok else None)
    else:
        prim, prim_name, sec, sec_name = bda, f"BDA-IEO {bda['code']}", crea, (f"CREA {crea['code']}" if c_ok else None)
    vals, srcs = {}, {}
    for d, nm in ((prim, prim_name), (sec, sec_name)):
        if not d or not d.get("values"):
            continue
        for k, x in d["values"].items():
            if k not in vals:
                vals[k] = x["v"]; srcs[k] = nm
    approx = not (c_exact or b_exact)
    tag = lambda k: "crea" if (srcs.get(k) or "").startswith("CREA") else "bda_ieo"  # noqa: E731

    n = item["nutrition_and_sustainability"]
    old = {"kcal_per_100g": n["kcal_per_100g"], "water_percentage": n["water_percentage"],
           "edible_portion_percentage": n["edible_portion_percentage"], **{f"macros_per_100g.{k}": v for k, v in n["macros_per_100g"].items()}}
    new = {"kcal_per_100g": vals.get("kcal"), "water_percentage": vals.get("water"), "edible_portion_percentage": vals.get("edible"),
           "macros_per_100g.carbs_g": vals.get("carbs"), "macros_per_100g.sugars_g": vals.get("sugars"),
           "macros_per_100g.starch_g": vals.get("starch"), "macros_per_100g.proteins_g": vals.get("protein"),
           "macros_per_100g.fats_g": vals.get("fat"), "macros_per_100g.fiber_g": vals.get("fiber"),
           "macros_per_100g.salt_g": round(vals["sodium"] * 2.5 / 1000, 3) if vals.get("sodium") is not None else None}
    enriched = []
    for f, v in new.items():
        if v is None:
            continue
        ov = old.get(f)
        if ov is not None and abs(ov - v) > 0.5 and abs(ov - v) / max(abs(v), 1e-9) > 0.10:
            key = {"kcal_per_100g": "kcal", "water_percentage": "water", "edible_portion_percentage": "edible"}.get(f) or \
                  {"carbs_g": "carbs", "sugars_g": "sugars", "starch_g": "starch", "proteins_g": "protein", "fats_g": "fat", "fiber_g": "fiber"}.get(f.split(".")[-1])
            add_discrepancy(item, f"nutrition_and_sustainability.{f}", ov, v, srcs.get(key, prim_name))
        if "." in f:
            n["macros_per_100g"][f.split(".")[1]] = v
        else:
            n[f] = v
        enriched.append(f"nutrition_and_sustainability.{f}")
    if vals.get("kj") is not None:
        n["kj_per_100g"] = vals["kj"]; enriched.append("nutrition_and_sustainability.kj_per_100g")

    vit, mins = [], []
    for k, (it_n, en_n, *_rest, typ) in NAMES.items():
        if k not in vals or typ == "b" or not vals[k]:   # null/zero values not shown
            continue
        unit = (prim["values"].get(k) or (sec or {}).get("values", {}).get(k) or {}).get("u") or NRV.get(k, (0, "mg"))[1]
        ref = NRV.get(k)
        e = {"name": it_n, "name_en": en_n, "amount": vals[k], "unit": unit if unit in ("g", "mg", "µg") else NRV.get(k, (0, "mg"))[1],
             "percent_nrv": round(vals[k] / ref[0] * 100, 1) if ref else None, "source": tag(k)}
        (vit if typ == "v" else mins).append(e)
    # bioactive compounds from the draft: kept; beta-carotene from the source if present
    bio = [b for b in n.get("bioactive_compounds", []) if not b["name"].lower().startswith("beta-carotene")]
    if "beta_carotene" in vals:
        bio.insert(0, {"name": "Beta-carotene", "name_en": "Beta-carotene", "amount": vals["beta_carotene"], "unit": "µg",
                       "percent_nrv": None, "source": tag("beta_carotene")})
    drafted = {canon(x["name"]): x["amount"] for x in n["vitamins"] + n["minerals"] if canon(x["name"])}
    n["vitamins"], n["minerals"], n["bioactive_compounds"] = vit, mins, bio
    enriched += ["nutrition_and_sustainability.vitamins", "nutrition_and_sustainability.minerals"]
    for k, dv in drafted.items():
        sv = vals.get(k)
        if sv is not None and dv is not None and abs(dv - sv) > 0.05 and abs(dv - sv) / max(sv, 1e-9) > 0.25:
            add_discrepancy(item, f"nutrition_and_sustainability.micronutrients.{k}", dv, sv, srcs.get(k))
    n["nutrition_claims_eu"] = claims(vals)
    enriched.append("nutrition_and_sustainability.nutrition_claims_eu")
    basis = f"{prim_name}" + (f", integrato con {sec_name}" if sec_name and any(s == sec_name for s in srcs.values()) else "") + \
            ", valori per 100 g di parte edibile" + (" (alimento di riferimento approssimato: vedi note)" if approx else "")
    n["data_basis"] = basis
    enriched.append("nutrition_and_sustainability.data_basis")
    if approx:
        item["data_completeness"]["notes"] += f" Nutrizione: voce di composizione approssimata ({prim_name}: {(crea or bda).get('description') or ''})."
    item["sources_by_topic"]["nutrition_crea_url"] = crea["url"] if c_ok else item["sources_by_topic"]["nutrition_crea_url"]
    mark_enriched(item, enriched)
    return True


def main():
    db = load_json(DATA / "database.json")
    idx = {i["id"]: i for i in load_json(DATA / "items_index.json")["items"]}
    stats = {"ok": 0, "none": []}
    for b, block in iter_blocks(db["items"], 15):
        for it in block:
            s = idx[it["id"]]["sources"]
            crea = fetch_crea(s["crea"]["code"]) if s.get("crea") else None
            bda = fetch_bda(s["bda_ieo"]["code"]) if s.get("bda_ieo") else None
            if enrich(it, crea, bda, idx[it["id"]]):
                stats["ok"] += 1
            else:
                stats["none"].append(it["id"])
            finalize_completeness(it)
        save_json(DATA / "database.json", db)
        print(f"block {b}: saved ({stats['ok']} enriched so far)")
    print("without composition data:", stats["none"])


if __name__ == "__main__":
    main()

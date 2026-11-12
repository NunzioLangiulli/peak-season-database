"""Nutrizione da USDA FoodData Central (SR Legacy) per gli alimenti senza scheda CREA/BDA-IEO.

Fonte non italiana, dichiarata in data_basis. I carboidrati USDA sono "by difference" (fibra inclusa): qui si
riportano i carboidrati disponibili = carboidrati - fibra, per coerenza con CREA.
API: https://api.nal.usda.gov/fdc/v1/ (chiave FDC_API_KEY in .env, altrimenti DEMO_KEY).
Uso:  python scripts/enrich_fdc.py
"""
from common import CONFIG, DATA, RAW, cached_json, env, finalize_completeness, http_get, load_json, mark_enriched, save_json
from enrich_nutrition import NAMES, NRV, claims

TARGETS = {"cavolo_nero_black_kale": "Kale, raw", "cavolo_rapa_kohlrabi": "Kohlrabi, raw", "pastinaca_parsnip": "Parsnips, raw",
           "topinambur_jerusalem_artichoke": "Jerusalem-artichokes, raw"}
_NEW = load_json(CONFIG / "new_items_2026_11_05.json")
TARGETS.update({k: v["fdc"] for k, v in _NEW.items() if v.get("fdc")})  # aggiunti 2026-11-05
APPROX = {k for k, v in _NEW.items() if v.get("fdc_q") == "approx"}   # voce USDA di un prodotto affine
NUM = {"255": "water", "208": "kcal", "268": "kj", "203": "protein", "204": "fat", "205": "carbs_diff", "291": "fiber", "269": "sugars",
       "209": "starch", "307": "sodium", "306": "potassium", "301": "calcium", "304": "magnesium", "305": "phosphorus", "303": "iron",
       "309": "zinc", "312": "copper", "315": "manganese", "317": "selenium", "401": "vit_c", "404": "vit_b1", "405": "vit_b2",
       "406": "niacin", "415": "vit_b6", "417": "folate", "418": "vit_b12", "320": "vit_a", "323": "vit_e", "430": "vit_k", "328": "vit_d",
       "321": "beta_carotene"}
KEY = env("FDC_API_KEY") or "DEMO_KEY"


def local_food(desc):
    """Stessa voce dalla copia locale di SR Legacy (data/raw/fdc_sr_legacy/sr_legacy.zip), se l'API non risponde."""
    import csv
    import io
    import zipfile
    from enrich_bioactives import PRE, ZIP
    z = zipfile.ZipFile(ZIP)
    rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(PRE + n), encoding="utf-8"))  # noqa: E731
    fid = next((r["fdc_id"] for r in rd("food.csv") if r["description"].lower() == desc.lower()), None)
    if not fid:
        return None
    num = {r["id"]: r["nutrient_nbr"] for r in rd("nutrient.csv")}
    nuts = [{"nutrientNumber": num.get(r["nutrient_id"]), "value": float(r["amount"])} for r in rd("food_nutrient.csv")
            if r["fdc_id"] == fid and r["amount"]]
    return {"fdcId": int(fid), "description": desc, "foodNutrients": nuts, "source": "sr_legacy_local"}


def fetch(desc):
    def go():
        try:
            r = http_get("https://api.nal.usda.gov/fdc/v1/foods/search", params={"api_key": KEY, "query": desc, "dataType": "SR Legacy", "pageSize": 5})
            foods = [f for f in r.json().get("foods", []) if f["description"].lower() == desc.lower()] or r.json().get("foods", [])[:1]
        except Exception:
            foods = []
        return foods[0] if foods else local_food(desc)
    return cached_json(RAW / "fdc_cache.json", desc, go)


def main():
    db = load_json(DATA / "database.json")
    for it in db["items"]:
        if it["id"] not in TARGETS:
            continue
        f = fetch(TARGETS[it["id"]])
        if not f:
            print("non trovato:", it["id"]); continue
        v = {}
        for nu in f.get("foodNutrients", []):
            k = NUM.get(str(nu.get("nutrientNumber")))
            if k and nu.get("value") is not None and k not in v:
                v[k] = nu["value"]
        if "carbs_diff" in v:
            v["carbs"] = round(v["carbs_diff"] - v.get("fiber", 0), 1)
        n = it["nutrition_and_sustainability"]
        n["data_basis"] = (f"USDA FoodData Central SR Legacy fdcId {f['fdcId']} '{f['description']}' (fonte non italiana: nessuna scheda CREA/BDA-IEO"
                           + ("; voce di un prodotto affine, approssimazione" if it["id"] in APPROX else "")
                           + "), per 100 g di parte edibile; carboidrati disponibili = by difference - fibra")
        n["kcal_per_100g"], n["kj_per_100g"], n["water_percentage"] = v.get("kcal"), v.get("kj"), v.get("water")
        m = n["macros_per_100g"]
        m.update({"carbs_g": v.get("carbs"), "sugars_g": v.get("sugars"), "starch_g": v.get("starch"), "proteins_g": v.get("protein"),
                  "fats_g": v.get("fat"), "fiber_g": v.get("fiber"), "salt_g": round(v["sodium"] * 2.5 / 1000, 3) if "sodium" in v else None})
        vit, mins = [], []
        for k, (it_n, en_n, *_r, typ) in NAMES.items():
            if not v.get(k) or typ == "b":
                continue
            ref = NRV.get(k)
            e = {"name": it_n, "name_en": en_n, "amount": v[k], "unit": ref[1] if ref else "mg",
                 "percent_nrv": round(v[k] / ref[0] * 100, 1) if ref else None, "source": "usda_fdc"}
            (vit if typ == "v" else mins).append(e)
        n["vitamins"], n["minerals"] = vit, mins
        n["nutrition_claims_eu"] = claims(v)
        n.setdefault("edible_portion_percentage", None)
        it["sources_by_topic"]["other_urls"].append(f"https://fdc.nal.usda.gov/food-details/{f['fdcId']}/nutrients")
        mark_enriched(it, ["nutrition_and_sustainability"])
        it["data_completeness"]["notes"] += " Nutrizione da USDA FoodData Central (nessuna scheda italiana disponibile)."
        finalize_completeness(it)
        print(it["id"], "kcal", v.get("kcal"), "prot", v.get("protein"), "fibra", v.get("fiber"), "| claim:", n["nutrition_claims_eu"]["it"][:4])
    save_json(DATA / "database.json", db)


if __name__ == "__main__":
    main()

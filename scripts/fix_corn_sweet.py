"""Owner decision 2026-11-04: in the app maize is the FRESH COB (sweet corn, Zea mays var. saccharata).

Before, the record mixed two products: nutrition from dry grain (CREA 000060 'Mais', BDA-IEO 3 'MAIS, crudo',
FDC 170288 'Corn grain, yellow') and storage/seasonality of sweet corn (UC Davis, HB66, EUFIC 'sweet corn').
This script:
- nutrition -> BDA-IEO 50086 'MAIS DOLCE, crudo' (exact match). CREA only has 'Mais, dolce, in scatola,
  sgocciolato' (000070): not used, because the canned product is salted and heat-treated.
- carotenoids -> FDC 169998 'Corn, sweet, yellow, raw' (map in enrich_bioactives.py, to re-run afterwards).
- category 'cereali' -> 'verdura' (eaten as a fresh vegetable).
- varieties Marano, Biancoperla, Ottofile = grain/polenta maize: removed from the record, kept in draft_legacy_values.
- nutritional discrepancies recomputed against the draft values (which already described sweet corn).
Usage:  python scripts/fix_corn_sweet.py   (then enrich_bioactives, enrich_protein, apply_texts, build_source_registry, tidy_notes)
"""
import re

from common import DATA, ROOT, finalize_completeness, load_json, save_json
from enrich_nutrition import enrich, fetch_bda

ID = "mais_corn"
BDA = "50086"
CREA_NOTE = ("CREA ha solo 'Mais, dolce, in scatola, sgocciolato' (000070), non usato: prodotto salato e trattato; "
             "nutrizione da BDA-IEO 50086 'MAIS DOLCE, crudo'")


def main():
    # --- catalogo e indice
    cat_p = ROOT / "scripts" / "config" / "catalog.json"
    cat = load_json(cat_p)
    entries = cat["items"] if isinstance(cat, dict) and "items" in cat else cat
    for e in entries:
        if e.get("id") == ID:
            e.update({"crea": None, "crea_q": None, "crea_note": CREA_NOTE, "bda": BDA, "bda_q": "exact"})
    save_json(cat_p, cat)

    idx = load_json(DATA / "items_index.json")
    ie = next(i for i in idx["items"] if i["id"] == ID)
    ie["category"] = "verdura"
    ie["sources"]["crea"] = None
    ie["sources"]["crea_note"] = CREA_NOTE
    ie["sources"]["bda_ieo"] = {"code": BDA, "name": "MAIS DOLCE, crudo", "match": "exact", "url": "https://bda.ieo.it/?page_id=87",
                                "api": {"endpoint": "https://bda.ieo.it/api/BDA/FoodComponents", "method": "POST",
                                        "body": {"language": 0, "foodId": f"<idFood da SearchFoodByCode '{BDA}'>"}}}
    save_json(DATA / "items_index.json", idx)

    # --- database
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    draft = next(i for i in load_json(DATA / "_backup_bozza_2026-11-04" / "database.json")["items"] if i["id"] == ID)
    it = next(i for i in db["items"] if i["id"] == ID)
    it["category"] = "verdura"
    dc = it["data_completeness"]
    n = it["nutrition_and_sustainability"]

    # draft values (sweet corn) as the comparison term for discrepancies
    dn = draft["nutrition_and_facts"]
    dm = dn["macros_per_100g"]
    n["kcal_per_100g"], n["water_percentage"], n["edible_portion_percentage"] = dn["kcal_per_100g"], dm.get("water_g"), dn["edible_portion_percentage"]
    for k in ("carbs_g", "sugars_g", "proteins_g", "fats_g", "fiber_g"):
        n["macros_per_100g"][k] = dm.get(k)
    n["macros_per_100g"]["starch_g"] = n["macros_per_100g"]["salt_g"] = None
    n["vitamins"] = [{"name": v["name"], "amount": v["amount"], "unit": v["unit"]} for v in dn["vitamins"]]
    n["minerals"] = [{"name": v["name"], "amount": v["amount"], "unit": v["unit"]} for v in dn["minerals"]]
    dc["discrepancies"] = [d for d in dc["discrepancies"] if not d["field"].startswith("nutrition_and_sustainability")]
    dc["notes"] = " ".join(s for s in re.split(r"(?<=\.)\s+(?=[A-ZÀ-Ý])", dc["notes"])
                           if not re.search(r"000060|170288|granella|Nutrizione: voce di composizione approssimata|Composti bioattivi:", s))

    bda = fetch_bda(BDA)
    if not bda["values"]:
        raise SystemExit("BDA-IEO 50086 without values")
    enrich(it, None, bda, ie)
    for v in n["vitamins"] + n["minerals"]:
        v.setdefault("source", "bda_ieo")

    sb = it["sources_by_topic"]
    sb["nutrition_crea_url"] = None
    sb["other_urls"] = [u for u in sb["other_urls"] if "fdc.nal.usda.gov/food-details/170288" not in u]
    sc = sb["source_codes"]
    sc.update({"crea": None, "crea_match": None, "bda_ieo": BDA, "bda_ieo_match": "exact"})

    # grain varieties -> legacy
    iv = it["italian_varieties_and_territories"]
    if iv["notable_varieties"]:
        legacy["items"].setdefault(ID, {})["italian_varieties_and_territories.grain_corn_varieties_removed"] = {
            "varieties": iv["notable_varieties"], "verification": iv.get("varieties_verification", []),
            "reason": "Varieta' verificate (Slow Food, Orto da Coltivare) ma di mais da granella/polenta, non di mais dolce: "
                      "la scheda descrive la pannocchia fresca (decisione utente 2026-11-04)."}
        iv["notable_varieties"], iv["varieties_verification"] = [], []
    dc["notes"] += (" Scheda riferita alla pannocchia fresca di mais dolce (decisione utente 2026-11-04): nutrizione da BDA-IEO "
                    f"{BDA} 'MAIS DOLCE, crudo'; le varieta' Marano, Biancoperla e Ottofile (mais da granella) sono state "
                    "spostate in draft_legacy_values. Attenzione: la voce BDA-IEO (dati McCance & Widdowson 2015) riporta "
                    "64 kcal e 8,1 g di carboidrati disponibili (amido 5,9 g, zuccheri 2,0 g), mentre USDA FDC 169998 'Corn, "
                    "sweet, yellow, raw' riporta 86 kcal e 18,7 g di carboidrati per differenza (amido 5,7 g, zuccheri 6,3 g): "
                    "l'amido coincide, la differenza sta negli zuccheri (che calano rapidamente dopo la raccolta) e nel "
                    "metodo di calcolo dei carboidrati.")
    finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print("kcal", n["kcal_per_100g"], "water", n["water_percentage"], "macros", n["macros_per_100g"], "claims", n["nutrition_claims_eu"]["it"])
    print("discrepancies:", [(d["field"], d.get("draft_value"), d.get("source_value")) for d in dc["discrepancies"] if d["field"].startswith("nutrition")])


if __name__ == "__main__":
    main()

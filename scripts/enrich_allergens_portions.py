"""Allergeni (Reg. UE 1169/2011, All. II) e porzione standard di riferimento (IEO SmartFood / LARN-SINU).

nutrition_and_sustainability.allergens_eu: lista di {annex_ii_number, name{it,en}} ([] = nessun allergene dell'allegato II)
nutrition_and_sustainability.reference_portion: {grams, group{it,en}, equivalent{it,en}, frequency{it,en}, kcal,
    proteins_g, fiber_g, source, match}. La castagna fresca usa la porzione della frutta (approssimata).
Uso:  python scripts/enrich_allergens_portions.py
"""
from common import DATA, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na

N = "nutrition_and_sustainability"
SRC = "https://www.smartfood.ieo.it/media/p02bkul0/smartfood-tab-porzioni-e-frequenze-completa.pdf"
EURLEX = "https://eur-lex.europa.eu/legal-content/IT/TXT/HTML/?uri=CELEX:02011R1169-20180101"
COOKED = {"spinacio_spinach", "bietola_da_coste_swiss_chard", "bietola_da_taglio_leaf_beet", "broccolo_broccoli", "cavolfiore_cauliflower",
          "melanzana_eggplant", "cavolo_nero_black_kale", "cima_di_rapa_turnip_greens", "cicoria_da_cespo_chicory",
          "cicoria_da_taglio_cutting_chicory", "scarola_escarole", "cavoletto_di_bruxelles_brussels_sprout", "cardo_cardoon",
          "cavolo_verza_savoy_cabbage", "cavolo_cappuccio_cabbage", "cavolo_rosso_red_cabbage"}


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "allergens_portions.json")
    db = load_json(DATA / "database.json")
    grp_of = {i: g for g, ids in cfg["item_group"].items() if not g.startswith("_") for i in ids}
    approx = set(cfg["item_group"]["_approx"])
    stats = {}
    for it in db["items"]:
        n = it[N]
        iid = it["id"]
        # --- allergeni
        codes = cfg["allergens"].get(iid, [])
        n["allergens_eu"] = [{"annex_ii_number": int(c), "name": {"it": cfg["annex_ii"][c][0], "en": cfg["annex_ii"][c][1]}} for c in codes]
        note = cfg["allergen_notes"].get(iid)
        n["allergens_note"] = {"it": note[0], "en": note[1]} if note else None
        if not note:
            set_na(it, [f"{N}.allergens_note"])
        mark_enriched(it, [f"{N}.allergens_eu"])
        if EURLEX not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append(EURLEX)
        # --- porzione
        g = grp_of.get(iid) or ("frutta" if it["category"] == "frutta" else "verdure")
        grams, g_it, g_en, f_it, f_en = cfg["groups"][g]
        eq = cfg["equivalents"].get(iid) or (
            cfg["equivalents"]["_salad"] if g == "insalate" else cfg["equivalents"]["_fruit"] if g == "frutta" else
            cfg["equivalents"]["_cooked_leafy"] if (g == "verdure" and iid in COOKED) else cfg["equivalents"].get(f"_{g}"))
        if grams is None:
            n["reference_portion"] = {"grams": None, "group": {"it": g_it, "en": g_en}, "equivalent": None,
                                      "frequency": {"it": f_it, "en": f_en}, "kcal": None, "proteins_g": None, "fiber_g": None,
                                      "source": SRC, "match": "exact"}
            set_na(it, [f"{N}.reference_portion.{k}" for k in ("grams", "equivalent", "kcal", "proteins_g", "fiber_g")])
        else:
            m = n["macros_per_100g"]
            f = grams / 100
            r = lambda v: None if v is None else round(v * f, 1)  # noqa: E731
            n["reference_portion"] = {
                "grams": grams, "group": {"it": g_it, "en": g_en},
                "equivalent": {"it": eq[0], "en": eq[1]} if eq else None, "frequency": {"it": f_it, "en": f_en},
                "kcal": None if n.get("kcal_per_100g") is None else round(n["kcal_per_100g"] * f),
                "proteins_g": r(m.get("proteins_g")), "fiber_g": r(m.get("fiber_g")), "source": SRC,
                "match": "approx" if iid in approx else "exact"}
            if not eq:
                set_na(it, [f"{N}.reference_portion.equivalent"])
        mark_enriched(it, [f"{N}.reference_portion"])
        stats[g] = stats.get(g, 0) + 1
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print("porzioni per gruppo:", stats)
    print("con allergeni:", [it["id"] for it in db["items"] if it[N]["allergens_eu"]])


if __name__ == "__main__":
    main()

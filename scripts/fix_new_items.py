"""Fixes for the products added on 2026-11-05 (config/new_items_2026_11_05.json). Idempotent.

Fridge storage time: if the product has no FoodKeeper entry, the "fridge" time assigned from HB66 is actually
the time under commercial conditions (0 °C, optimal humidity): it is moved to commercial_optimal_days and the home
time stays empty (same rule already applied to Jerusalem artichoke, loquat, quince and truffle).
Missing nutrition: for products without a CREA, BDA-IEO or USDA record the data_basis field says so
(values stay empty, as for white truffle); if there are only vitamins and minerals from a related USDA entry
(fill_micros_fdc.py) this is stated.
Usage:  python scripts/fix_new_items.py   (after apply_foodkeeper_modes.py and fill_micros_fdc.py)
"""
from common import CONFIG, DATA, RAW, finalize_completeness, load_json, save_json


def main():
    db = load_json(DATA / "database.json")
    new = load_json(CONFIG / "new_items_2026_11_05.json")
    fk = load_json(RAW / "foodkeeper_produce.json")["mapping"]
    moved = []
    for it in db["items"]:
        if it["id"] not in new or it["id"] in fk:
            continue
        sl = it["ripening_and_storage"]["postharvest_physiology"]["estimated_shelf_life_days"]
        if sl.get("refrigerated_days"):
            if not sl.get("commercial_optimal_days"):
                sl["commercial_optimal_days"] = sl["refrigerated_days"]
            sl["refrigerated_days"] = None
            moved.append(it["id"])
            finalize_completeness(it)
    nonut = []
    for it in db["items"]:
        n = it["nutrition_and_sustainability"]
        if it["id"] not in new or n.get("kcal_per_100g") is not None:
            continue
        micro = bool(n.get("vitamins") or n.get("minerals"))
        fdc = (new[it["id"]].get("fdc_id") or [None, None, None])
        it_txt = ("Nessuna scheda di composizione in CREA, BDA-IEO o USDA per questo alimento: valori nutrizionali non disponibili da fonti ufficiali."
                  + (f" Vitamine e minerali indicativi dalla voce USDA affine '{fdc[2]}' (approssimazione)." if micro and fdc[2] else ""))
        en_txt = ("No composition data in CREA, BDA-IEO or USDA for this food: nutrition values not available from official sources."
                  + (f" Indicative vitamins and minerals from the related USDA entry '{fdc[2]}' (approximation)." if micro and fdc[2] else ""))
        n["data_basis"] = {"it": it_txt, "en": en_txt}
        nonut.append(it["id"])
    save_json(DATA / "database.json", db)
    print("durate professionali spostate:", moved, "| nutrizione dichiarata non disponibile:", nonut)


if __name__ == "__main__":
    main()

"""HOME storage times from USDA FSIS FoodKeeper (data/raw/foodkeeper_produce.json).

- room_temp_days      <- pantry (from the date of purchase)
- refrigerated_days   <- home fridge; the USDA HB66 commercial storage time (previously in refrigerated_days) is
                         moved to commercial_optimal_days
- in_freezer_months   <- freezer
Values missing in FoodKeeper = storage not stated: the previous (draft) value stays, to be verified.
Usage:  python scripts/enrich_foodkeeper.py
"""
import re

from common import DATA, RAW, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json

F = {"D": 1, "W": 7, "M": 30, "Y": 365}


def days(v):
    if not v:
        return None
    a, b, u = re.match(r"(\d+)-(\d+)([DWMY])", v).groups()
    return [int(a) * F[u], int(b) * F[u]]


def months(v):
    d = days(v)
    return None if d is None else round(d[1] / 30, 1)


def main():
    fk = load_json(RAW / "foodkeeper_produce.json")
    db = load_json(DATA / "database.json")
    n = 0
    for it in db["items"]:
        pid = fk["mapping"].get(it["id"])
        sl = it["ripening_and_storage"]["postharvest_physiology"]["estimated_shelf_life_days"]
        if "commercial_optimal_days" not in sl:
            sl["commercial_optimal_days"] = None
            sl["basis"] = None
        if not pid:
            finalize_completeness(it)
            continue
        name, pantry, fridge, freezer = fk["products"][str(pid)]
        enr = []
        P = "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days"
        if "HB66" in it["data_completeness"]["notes"] and sl["refrigerated_days"] and sl["commercial_optimal_days"] is None:
            sl["commercial_optimal_days"] = sl["refrigerated_days"]
            enr.append(f"{P}.commercial_optimal_days")
        for key, val in (("room_temp_days", days(pantry)), ("refrigerated_days", days(fridge))):
            if val:
                old = sl[key]
                if old and old != val and key == "room_temp_days":
                    add_discrepancy(it, f"{P}.{key}", old, val, f"USDA FoodKeeper ({name})")
                sl[key] = val
                enr.append(f"{P}.{key}")
        if freezer:
            if sl["in_freezer_months"] is not None and abs(sl["in_freezer_months"] - months(freezer)) > 1:
                add_discrepancy(it, f"{P}.in_freezer_months", sl["in_freezer_months"], months(freezer), f"USDA FoodKeeper ({name})")
            sl["in_freezer_months"] = months(freezer)
            enr.append(f"{P}.in_freezer_months")
        sl["basis"] = f"Durate domestiche: USDA FoodKeeper '{name}' (dalla data di acquisto); commercial_optimal_days: USDA HB66 / UC Davis in condizioni professionali."
        enr.append(f"{P}.basis")
        if "https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json" not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append("https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json")
        mark_enriched(it, enr)
        finalize_completeness(it)
        n += 1
    save_json(DATA / "database.json", db)
    print("products with FoodKeeper storage times:", n)


if __name__ == "__main__":
    main()

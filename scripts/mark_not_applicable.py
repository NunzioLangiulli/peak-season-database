"""Marks non-applicable fields (not_applicable_fields), so the report can tell real gaps apart.

- Dried products (cereals, dried legumes, peanuts, dried oregano): respiration, ethylene and fridge storage time
  not applicable (the draft value goes to draft_legacy_values.json).
- Agricultural calendar of the vegetables in the Orto da Coltivare tables: a sowing/transplanting method that ODC
  does not give for that zone (null field) is "not planned", not missing data.
- Products without Italian production (exotic): agricultural calendar and agronomic parameters not applicable.
Usage:  python scripts/mark_not_applicable.py
"""
from apply_texts import DRY
from common import DATA, finalize_completeness, load_json, save_json
from enrich_chilling import set_na

P = "ripening_and_storage.postharvest_physiology"
E = "ripening_and_storage.ethylene_compatibility"
A = "agricultural_calendar_italy"


def main():
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    st = {"secchi": 0, "odc": 0, "esotici": 0}
    for it in db["items"]:
        iid = it["id"]
        if iid in DRY:
            ph = it["ripening_and_storage"]["postharvest_physiology"]
            ec = it["ripening_and_storage"]["ethylene_compatibility"]
            for obj, key, path in ((ph, "respiration_rate_class", f"{P}.respiration_rate_class"),
                                   (ec, "produces_ethylene", f"{E}.produces_ethylene"),
                                   (ec, "sensitive_to_ethylene", f"{E}.sensitive_to_ethylene"),
                                   (ec, "ethylene_production_class", f"{E}.ethylene_production_class"),
                                   (ph["estimated_shelf_life_days"], "refrigerated_days", f"{P}.estimated_shelf_life_days.refrigerated_days")):
                if obj.get(key) is not None:
                    legacy["items"].setdefault(iid, {})[path] = obj[key]
                obj[key] = None
                set_na(it, [path])
            ec["keep_away_from"] = []
            st["secchi"] += 1
        cal = it[A]
        if it["sources_by_topic"].get("source_codes", {}).get("odc_pdf_row"):
            paths = [f"{A}.{z}.{k}" for z in ("nord", "centro", "sud_isole")
                     for k in ("seedbed_sowing_months", "direct_sowing_months", "transplant_months") if cal[z].get(k) is None]
            if paths:
                set_na(it, paths)
                st["odc"] += 1
        if "senza produzione italiana" in it["data_completeness"]["notes"] or it["seasonality"].get("italy_national") == "not_applicable":
            paths = []

            def walk(o, p):
                if isinstance(o, dict):
                    for k, v in o.items():
                        walk(v, f"{p}.{k}")
                elif o is None:
                    paths.append(p)
            walk(cal, A)
            if paths:
                set_na(it, paths)
                st["esotici"] += 1
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(st)


if __name__ == "__main__":
    main()

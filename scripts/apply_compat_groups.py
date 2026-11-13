"""Compatible storage group (USDA HB66, Table 1 'Compatible fresh fruits and vegetables during 7-day storage',
Thompson et al. 1996) -> ripening_and_storage.storage_compatibility.

compatible_with = products of the same group (same temperature/humidity), excluding pairings discouraged because of
ethylene (keep_away_from in both directions). Dried and unlisted products: null (not applicable).
Usage:  python scripts/apply_compat_groups.py   (after apply_hb66_curated.py, which recomputes keep_away_from)
"""
from common import DATA, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na

URL = "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf#page=65"
P = "ripening_and_storage.storage_compatibility"


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "hb66_compatibility_groups.json")
    db = load_json(DATA / "database.json")
    kaf = {it["id"]: set(it["ripening_and_storage"]["ethylene_compatibility"].get("keep_away_from") or []) for it in db["items"]}
    by_group = {}
    for iid, (g, *_r) in cfg["items"].items():
        by_group.setdefault(g, []).append(iid)
    n = 0
    for it in db["items"]:
        m = cfg["items"].get(it["id"])
        r = it["ripening_and_storage"]
        if not m:
            r["storage_compatibility"] = None
            set_na(it, [P])
            finalize_completeness(it)
            continue
        g, match, entry = m
        meta = cfg["groups"][g]
        same = [x for x in by_group[g] if x != it["id"] and x not in kaf[it["id"]] and it["id"] not in kaf.get(x, set())]
        r["storage_compatibility"] = {
            "group": g, "label": {"it": meta["it"], "en": meta["en"]}, "temperature_c": {"min": meta["temp_c"][0], "max": meta["temp_c"][1]},
            "humidity_percent": {"min": meta["rh"][0], "max": meta["rh"][1]}, "table_entry": entry, "match": match,
            "compatible_with": sorted(same), "source": URL}
        mark_enriched(it, [P])
        if URL not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append(URL)
        n += 1
        finalize_completeness(it)
    db["metadata"]["storage_compatibility_legend"] = {
        "basis": "USDA HB66, Table 1 (Thompson et al. 1996): prodotti che possono stare insieme per 7 giorni; etilene < 1 ppm.",
        "groups": {k: {"it": v["it"], "en": v["en"], "temperature_c": v["temp_c"], "humidity_percent": v["rh"]} for k, v in cfg["groups"].items()}}
    save_json(DATA / "database.json", db)
    print(f"gruppo di compatibilita' assegnato a {n} alimenti; per gruppo:", {k: len(v) for k, v in by_group.items()})


if __name__ == "__main__":
    main()

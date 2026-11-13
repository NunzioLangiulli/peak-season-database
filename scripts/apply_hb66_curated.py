"""Applies the values transcribed by hand from the USDA HB66 chapters (config/hb66_chapter_curated.json).
Every value differing from the current one becomes a discrepancy; non-applicable fields (chilling-injury threshold of
non-sensitive products) go to not_applicable_fields. keep_away_from is recomputed for sensitive products.
Usage:  python scripts/apply_hb66_curated.py
"""
from common import CONFIG, DATA, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na

P = "ripening_and_storage.postharvest_physiology"
E = "ripening_and_storage.ethylene_compatibility"


def main():
    cfg = load_json(CONFIG / "hb66_chapter_curated.json")
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    producers = sorted(i["id"] for i in db["items"]
                       if i["ripening_and_storage"]["ethylene_compatibility"].get("ethylene_production_class") in ("high", "very_high"))
    n = 0
    for it in db["items"]:
        c = cfg["items"].get(it["id"])
        if not c:
            continue
        ph = it["ripening_and_storage"]["postharvest_physiology"]
        ec = it["ripening_and_storage"]["ethylene_compatibility"]
        sl = ph["estimated_shelf_life_days"]
        ci = ph["chilling_injury"]
        src = f"USDA HB66, capitolo '{c['chapter']}'" + (f" p. {c['page']}" if c.get("page") else "")
        enr = []

        def put(obj, key, path, val):
            old = obj.get(key)
            if old is not None and old != val:
                add_discrepancy(it, path, old, val, src)
            obj[key] = val
            enr.append(path)

        for key, obj, path in (("optimal_temperature_c", ph, f"{P}.optimal_temperature_c"),
                               ("optimal_humidity_percent", ph, f"{P}.optimal_humidity_percent"),
                               ("freezing_point_c", ph, f"{P}.freezing_point_c"),
                               ("respiration_rate_class", ph, f"{P}.respiration_rate_class"),
                               ("commercial_optimal_days", sl, f"{P}.estimated_shelf_life_days.commercial_optimal_days"),
                               ("produces_ethylene", ec, f"{E}.produces_ethylene"),
                               ("ethylene_production_class", ec, f"{E}.ethylene_production_class"),
                               ("sensitive_to_ethylene", ec, f"{E}.sensitive_to_ethylene")):
            if key in c:
                put(obj, key, path, c[key])
        if "chilling_susceptible" in c:
            put(ci, "susceptible", f"{P}.chilling_injury.susceptible", c["chilling_susceptible"])
            if c["chilling_susceptible"] is False:
                for k in ("critical_temperature_c", "symptoms"):
                    if ci.get(k) is not None:
                        legacy["items"].setdefault(it["id"], {})[f"{P}.chilling_injury.{k}"] = ci[k]
                ci.update({"critical_temperature_c": None, "symptoms": None, "lowest_safe_range_c": None})
                set_na(it, [f"{P}.chilling_injury.critical_temperature_c", f"{P}.chilling_injury.symptoms", f"{P}.chilling_injury.lowest_safe_range_c"])
            else:
                for k in ("critical_temperature_c", "lowest_safe_range_c", "symptoms"):
                    if k in c:
                        put(ci, k, f"{P}.chilling_injury.{k}", c[k])
                if "critical_temperature_c" in c and c["critical_temperature_c"] is None:
                    # injury within a temperature band (e.g. stone fruit 2-8 °C), not below a single threshold
                    set_na(it, [f"{P}.chilling_injury.critical_temperature_c"])
                    enr.remove(f"{P}.chilling_injury.critical_temperature_c")
        if "sensitive_to_ethylene" in c:
            ec["keep_away_from"] = [p for p in producers if p != it["id"]] if c["sensitive_to_ethylene"] else []
            enr.append(f"{E}.keep_away_from")
        if c.get("resp_basis"):
            it["data_completeness"]["notes"] += f" Respirazione: {c['resp_basis']} ({src})."
        if c.get("match") == "approx":
            it["data_completeness"]["notes"] += f" Dati post-raccolta dal capitolo HB66 '{c['chapter']}' (prodotto affine)."
        if c.get("sensitive_to_ethylene", 0) is None:
            ec["sensitive_to_ethylene"] = None
            enr.remove(f"{E}.sensitive_to_ethylene")
            it["data_completeness"]["fields_pending_verification"] = [
                p for p in it["data_completeness"].get("fields_pending_verification", []) if p != f"{E}.sensitive_to_ethylene"]
            it["data_completeness"]["notes"] += " Sensibilità all'etilene: USDA HB66 dichiara che non esistono dati."
        mark_enriched(it, enr)
        finalize_completeness(it)
        n += 1
    # keep_away_from recomputed for all: high/very_high producers updated (e.g. pear)
    producers = sorted(i["id"] for i in db["items"]
                       if i["ripening_and_storage"]["ethylene_compatibility"].get("ethylene_production_class") in ("high", "very_high"))
    for it in db["items"]:
        ec = it["ripening_and_storage"]["ethylene_compatibility"]
        ec["keep_away_from"] = [p for p in producers if p != it["id"]] if ec.get("sensitive_to_ethylene") is True else []
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print("alimenti aggiornati da capitoli HB66:", n, "| produttori di etilene:", producers)


if __name__ == "__main__":
    main()

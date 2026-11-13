"""Chilling injury and freezing susceptibility from USDA HB66 (tables transcribed in config/hb66_chilling_freezing.json).

- Tab. 1 (lowest safe temperature): susceptible=True, lowest_safe_range_c, critical_temperature_c = upper end
  (cautious), IT/EN symptoms. A different draft value becomes a discrepancy.
- Products with chilling_injury.susceptible=False already verified: threshold and symptoms not applicable -> null and
  not_applicable_fields (the draft value, often a freezing point, goes to draft_legacy_values.json).
- Dried products (seeds, cereals, dried legumes, dried herbs): chilling injury not applicable.
- Tab. 2: freezing_susceptibility most/moderate/least.
Usage:  python scripts/enrich_chilling.py
"""
from apply_texts import DRY
from common import CONFIG, DATA, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json

P = "ripening_and_storage.postharvest_physiology"
C = f"{P}.chilling_injury"
SRC = "USDA HB66 'Chilling and Freezing Injury'"


def set_na(it, paths):
    dc = it["data_completeness"]
    dc["not_applicable_fields"] = sorted(set(dc.get("not_applicable_fields", [])) | set(paths))
    dc["fields_pending_verification"] = [p for p in dc.get("fields_pending_verification", [])
                                         if not any(p == q or p.startswith(q + ".") for q in paths)]


def main():
    cfg = load_json(CONFIG / "hb66_chilling_freezing.json")
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    frz = {iid: (cls, m) for cls, g in cfg["freezing"].items() for iid, m in g["items"].items()}
    st = {"tab1": 0, "cultivar": 0, "na_non_sensibile": 0, "na_secco": 0, "gelo": 0, "discrepanze": 0}
    for it in db["items"]:
        iid = it["id"]
        ph = it["ripening_and_storage"]["postharvest_physiology"]
        ci = ph["chilling_injury"]
        ci.setdefault("lowest_safe_range_c", None)
        ph.setdefault("freezing_susceptibility", None)
        pend = set(it["data_completeness"].get("fields_pending_verification", []))
        enr = []
        row = cfg["chilling"].get(iid)
        if row:
            lo, hi = row["c"]
            old = ci["critical_temperature_c"]
            if old is not None and abs(old - hi) > 0.5:
                add_discrepancy(it, f"{C}.critical_temperature_c", old, hi, f"{SRC}, Tab. 1 riga '{row['row']}' ({lo}-{hi} °C)")
                st["discrepanze"] += 1
            if ci["susceptible"] is False:
                add_discrepancy(it, f"{C}.susceptible", False, True, f"{SRC}, Tab. 1 riga '{row['row']}'")
            note_it = f" ({row['note']})" if row.get("note") else ""
            ci.update({"susceptible": True, "critical_temperature_c": hi, "lowest_safe_range_c": {"min": lo, "max": hi},
                       "symptoms": {"it": row["sym_it"] + note_it, "en": row["sym_en"]}})
            enr += [f"{C}.susceptible", f"{C}.critical_temperature_c", f"{C}.lowest_safe_range_c", f"{C}.symptoms"]
            if row["match"] != "exact":
                it["data_completeness"]["notes"] += f" Danno da freddo: riga HB66 '{row['row']}' (prodotto affine)."
            st["tab1"] += 1
        elif iid in cfg["chilling_cultivar_dependent"]:
            r = cfg["chilling_cultivar_dependent"][iid]
            if ci["critical_temperature_c"] is not None:
                legacy["items"].setdefault(iid, {})[f"{C}.critical_temperature_c"] = ci["critical_temperature_c"]
            ci.update({"critical_temperature_c": None, "lowest_safe_range_c": {"min": r["c"][0], "max": r["c"][1]},
                       "symptoms": {"it": f"{r['sym_it']} ({r['note']})",
                                    "en": f"{r['sym_en']} (certain cultivars only: most apples are stored at -1 to 0 °C)"}})
            enr += [f"{C}.lowest_safe_range_c", f"{C}.symptoms"]
            set_na(it, [f"{C}.critical_temperature_c"])
            st["cultivar"] += 1
        elif iid in DRY:
            for k in ("critical_temperature_c", "symptoms"):
                if ci[k] is not None:
                    legacy["items"].setdefault(iid, {})[f"{C}.{k}"] = ci[k]
            ci.update({"susceptible": None, "critical_temperature_c": None, "symptoms": None})
            set_na(it, [f"{C}.susceptible", f"{C}.critical_temperature_c", f"{C}.symptoms", f"{C}.lowest_safe_range_c",
                        f"{P}.freezing_susceptibility", f"{P}.freezing_point_c"])
            it["data_completeness"]["notes"] += " Danno da freddo e gelo non pertinenti (prodotto secco)."
            st["na_secco"] += 1
        elif ci["susceptible"] is False and f"{C}.susceptible" not in pend:
            if ci["critical_temperature_c"] is not None:
                legacy["items"].setdefault(iid, {})[f"{C}.critical_temperature_c"] = ci["critical_temperature_c"]
                it["data_completeness"]["notes"] += (f" Soglia di danno da freddo della bozza ({ci['critical_temperature_c']} °C) rimossa:"
                                                     " l'alimento non è sensibile (valore probabilmente riferito al congelamento).")
            ci.update({"critical_temperature_c": None, "symptoms": None})
            set_na(it, [f"{C}.critical_temperature_c", f"{C}.symptoms", f"{C}.lowest_safe_range_c"])
            st["na_non_sensibile"] += 1
        elif ci["susceptible"] is True and f"{C}.critical_temperature_c" not in pend:
            set_na(it, [f"{C}.lowest_safe_range_c"])  # threshold already verified from the HB66 chapter / UC Davis
        if iid in frz:
            cls, m = frz[iid]
            ph["freezing_susceptibility"] = cls
            enr.append(f"{P}.freezing_susceptibility")
            if m != "exact":
                it["data_completeness"]["notes"] += " Sensibilità al gelo: gruppo HB66 di un prodotto affine."
            st["gelo"] += 1
        if enr:
            urls = it["sources_by_topic"]["postharvest_ucdavis_usda_url"]
            urls = [urls] if isinstance(urls, str) else (urls or [])
            if cfg["url"] not in urls:
                urls.append(cfg["url"])
            it["sources_by_topic"]["postharvest_ucdavis_usda_url"] = urls
        mark_enriched(it, enr)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(st)


if __name__ == "__main__":
    main()

"""Template fields empty by definition -> data_completeness.not_applicable_fields (with a reason).

- keep_away_from = [] if the product is not ethylene-sensitive (or the data are missing);
- dop_igp_labels = [] if has_dop_igp is false;
- dried products: optimal postharvest temperature/humidity (referring to fresh produce), ethylene compatibility notes,
  months in the freezer if FoodKeeper does not give them;
- tomato: no fridge (FoodKeeper and UC Davis: at room temperature);
- days at room temperature when the sources give only the fridge (UC Davis guide or HB66 chapter) and
  FoodKeeper gives no pantry time. The draft value goes to draft_legacy_values.
Usage:  python scripts/mark_structural_na.py   (after apply_home_storage.py)
"""
from common import DATA, finalize_completeness, load_json, save_json
from enrich_chilling import set_na

DRY = {"cece_chickpea", "lenticchia_lentil", "farro_emmer", "orzo_barley", "grano_duro_durum_wheat", "riso_rice", "avena_oat",
       "grano_saraceno_buckwheat", "arachide_peanut", "origano_oregano"}
P = "ripening_and_storage.postharvest_physiology"
E = "ripening_and_storage.ethylene_compatibility"
S = f"{P}.estimated_shelf_life_days"
# frigorifero indicato esplicitamente dal capitolo HB66 (citazioni in config/hb66_chapter_curated.json)
HB66_FRIDGE = {"finocchio_fennel": "HB66 Fennel: 'Fennel must be kept refrigerated'",
               "topinambur_jerusalem_artichoke": "HB66 Jerusalem Artichoke: 'displayed in refrigerated display cases'",
               "nespola_loquat": "HB66 Loquat: 'A refrigerated shelf at 5 to 12 °C is good'",
               "tartufo_nero_black_truffle": "HB66 Truffle: 'kept sealed in impermeable plastic trays in the cold section'"}


def main():
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    counts = {}

    def na(it, path, why, obj=None, key=None):
        dc = it["data_completeness"]
        if obj is not None and obj.get(key) not in (None, [], {}) and path in dc.get("fields_pending_verification", []):
            legacy["items"].setdefault(it["id"], {})[path] = obj[key]
        if obj is not None:
            obj[key] = None
        set_na(it, [path])
        counts[why] = counts.get(why, 0) + 1

    for it in db["items"]:
        r = it["ripening_and_storage"]
        ph, ec, sl = r["postharvest_physiology"], r["ethylene_compatibility"], r["postharvest_physiology"]["estimated_shelf_life_days"]
        iv = it["italian_varieties_and_territories"]
        dc = it["data_completeness"]
        if not ec.get("keep_away_from") and ec.get("sensitive_to_ethylene") is not True:
            set_na(it, [f"{E}.keep_away_from"]); counts["keep_away_from"] = counts.get("keep_away_from", 0) + 1
        if not iv.get("dop_igp_labels") and iv.get("has_dop_igp") is False:
            set_na(it, ["italian_varieties_and_territories.dop_igp_labels"]); counts["dop"] = counts.get("dop", 0) + 1
        if it["id"] in DRY:
            na(it, f"{P}.optimal_temperature_c", "dry_temp", ph, "optimal_temperature_c")
            na(it, f"{P}.optimal_humidity_percent", "dry_rh", ph, "optimal_humidity_percent")
            if not ec.get("compatibility_notes"):
                set_na(it, [f"{E}.compatibility_notes"])
            if sl.get("in_freezer_months") is None:
                set_na(it, [f"{S}.in_freezer_months"])
        if it["id"] == "pomodoro_tomato" and sl.get("refrigerated_days") is None:
            set_na(it, [f"{S}.refrigerated_days"])
            dc["notes"] += " Frigorifero non pertinente: USDA FoodKeeper e UC Davis indicano la conservazione a temperatura ambiente (il freddo ne spegne sapore e colore)."
        hs = r.get("home_storage") or {}
        if (sl.get("room_temp_mode") is None and hs.get("location") == "fridge"
                and (hs.get("ucdavis_group") == "refrigerator" or it["id"] in HB66_FRIDGE)):
            why = "guida UC Davis/Kader: 'Store in refrigerator'" if hs.get("ucdavis_group") else HB66_FRIDGE[it["id"]]
            sl["room_temp_mode"] = "fridge_only"
            na(it, f"{S}.room_temp_days", "fridge_only", sl, "room_temp_days")
            sl["basis"] = (sl.get("basis") or "") + f" Temperatura ambiente non indicata: le fonti prevedono solo il frigorifero ({why})."
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(counts)


if __name__ == "__main__":
    main()

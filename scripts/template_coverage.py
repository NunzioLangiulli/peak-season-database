"""Copertura dei campi del TEMPLATE ORIGINALE (prompt Fase 1) nel database attuale.

Per ogni campo del modello: verificato da fonte | solo bozza (da verificare) | non pertinente (N/A) | mancante (null).
Scrive data/template_coverage.json e stampa una tabella.
Uso:  python scripts/template_coverage.py
"""
from common import DATA, load_json, save_json

ZONES = ["nord", "centro", "sud_isole"]
F = (["botany.scientific_name", "botany.eppo_code", "botany.family", "botany.genus", "botany.plant_part_used",
      "italian_varieties_and_territories.notable_varieties", "italian_varieties_and_territories.has_dop_igp",
      "italian_varieties_and_territories.dop_igp_labels", "images.primary", "images.gallery",
      "seasonality.eufic_climatic_zones", "seasonality.italy_macro_areas"]
     + [f"agricultural_calendar_italy.{z}.{k}" for z in ZONES for k in ("sowing_or_transplant_months", "harvest_months")]
     + [f"agricultural_calendar_italy.agronomic_params.{k}" for k in
        ("sowing_depth_cm", "plant_spacing_cm.between_rows", "plant_spacing_cm.between_plants", "sun_exposure", "lunar_phase_advice")]
     + ["agricultural_calendar_italy.{z}.cultivation_notes".format(z=z) for z in ZONES]
     + ["buying_guide.shopping_list_preview", "buying_guide.detailed_selection",
        "ripening_and_storage.ripening_type", "ripening_and_storage.ripening_badge_label", "ripening_and_storage.card_short_storage",
        "ripening_and_storage.primary_location", "ripening_and_storage.storage_instructions"]
     + ["ripening_and_storage.postharvest_physiology." + k for k in
        ("optimal_temperature_c", "optimal_humidity_percent", "respiration_rate_class", "chilling_injury.susceptible",
         "chilling_injury.critical_temperature_c", "chilling_injury.symptoms", "estimated_shelf_life_days.room_temp_days",
         "estimated_shelf_life_days.refrigerated_days", "estimated_shelf_life_days.in_freezer_months")]
     + ["ripening_and_storage.ripening_management.slow_down", "ripening_and_storage.ripening_management.speed_up"]
     + ["ripening_and_storage.ethylene_compatibility." + k for k in
        ("produces_ethylene", "ethylene_production_class", "sensitive_to_ethylene", "keep_away_from", "compatibility_notes")]
     + ["nutrition_and_sustainability." + k for k in
        ("edible_portion_percentage", "water_percentage", "kcal_per_100g", "macros_per_100g.carbs_g", "macros_per_100g.sugars_g",
         "macros_per_100g.proteins_g", "macros_per_100g.fats_g", "macros_per_100g.fiber_g", "vitamins", "minerals",
         "nutrition_claims_eu", "health_benefits_and_curiosities", "culinary_waste_reduction")])


def get(o, path):
    for k in path.split("."):
        if not isinstance(o, dict) or k not in o:
            return None
        o = o[k]
    return o


def status(it, path):
    dc = it["data_completeness"]
    hit = lambda lst: any(p == path or p.startswith(path + ".") for p in lst)  # noqa: E731
    if hit(dc.get("not_applicable_fields", [])) and get(it, path) in (None, [], {}):
        return "na"
    v = get(it, path)
    if v is None or v == [] or (isinstance(v, dict) and v and all(x in (None, [], "") for x in v.values())):
        return "missing"
    if hit(dc.get("fields_pending_verification", [])):
        return "draft"
    return "ok"


def main():
    db = load_json(DATA / "database.json")
    out = {}
    for p in F:
        c = {"ok": [], "draft": [], "na": [], "missing": []}
        for it in db["items"]:
            c[status(it, p)].append(it["id"])
        out[p] = c
    save_json(DATA / "template_coverage.json", out)
    print(f"{'campo':72} ok draft  na miss")
    for p, c in out.items():
        if c["draft"] or c["missing"]:
            print(f"{p:72} {len(c['ok']):3} {len(c['draft']):4} {len(c['na']):3} {len(c['missing']):4}")
    full = [p for p, c in out.items() if not c["draft"] and not c["missing"]]
    print(f"\ncampi del template completi (ok o N/A per tutti gli alimenti): {len(full)}/{len(F)}")


if __name__ == "__main__":
    main()

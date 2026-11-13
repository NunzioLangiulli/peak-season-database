"""Step 1.2 - Migrates the owner's draft into the final structure (data/schema.json).

Input : data/_backup_bozza_2026-11-04/database.json  (original draft, never modified; not published)
        data/items_index.json                        (master index, Step 1.1)
        scripts/config/eufic_zone_map.json
Output: data/database.json                           (database v2, migrated)
        data/draft_legacy_values.json                (draft values NOT carried into the database,
                                                      kept in full for traceability)

Rules:
- no valid draft data is lost: it is either migrated into the new field or ends up in draft_legacy_values.json
  with the reason;
- values migrated from the draft are listed in data_completeness.fields_pending_verification until
  Step 1.3 compares them with the official sources;
- data enriched from the sources are NOT added here (only data already verified in the index: EPPO,
  WFO/GBIF codes and sheet URLs).

Usage:  python scripts/migrate_draft.py
"""
import datetime
import re

from common import CONFIG, DATA, load_json, save_json

DRAFT = DATA / "_backup_bozza_2026-11-04" / "database.json"
ZONES = ["mediterranean", "continental", "atlantic", "boreal", "mountain", "pannonian"]

PLANT_PART = {  # draft values outside the enum -> final enum
    "foglie": "foglia", "foglie_cespo": "foglia", "rosetta_fogliare": "foglia", "costole_foglie": "fusto_costa",
    "grumolo": "fusto_costa", "falso_fusto": "fusto_costa", "frutto_baccello": "frutto",
    "fungo_corpo_fruttifero": "fungo_carpoforo",
}
VITAMINS_EN = {
    "Vitamina C": "Vitamin C", "Tiamina (B1)": "Thiamin (B1)", "Riboflavina (B2)": "Riboflavin (B2)",
    "Vitamina B2 (Riboflavina)": "Riboflavin (B2)", "Niacina": "Niacin (B3)", "Niacina (B3)": "Niacin (B3)",
    "Vitamina B6": "Vitamin B6", "Folati": "Folate (B9)", "Folati (B9)": "Folate (B9)", "Vitamina A": "Vitamin A",
    "Vitamina A (retinolo eq.)": "Vitamin A (retinol eq.)", "Beta-carotene": "Beta-carotene",
    "Beta-carotene (Vit. A)": "Beta-carotene", "Vitamina E": "Vitamin E", "Vitamina K": "Vitamin K",
    "Vitamina D (Ergosterolo)": "Vitamin D (ergosterol)",
}
MINERALS_EN = {
    "Calcio": "Calcium", "Ferro": "Iron", "Fosforo": "Phosphorus", "Magnesio": "Magnesium", "Manganese": "Manganese",
    "Potassio": "Potassium", "Rame": "Copper", "Selenio": "Selenium", "Sodio": "Sodium", "Zinco": "Zinc",
}
FOLATE_NAMES = {"Folati", "Folati (B9)"}


def leaf_paths(obj, prefix=""):
    """Leaf paths ('a.b.c' strings) with null / non-null value. Lists of objects = a single leaf."""
    if isinstance(obj, dict):
        if not obj:
            yield prefix, obj
        for k, v in obj.items():
            yield from leaf_paths(v, f"{prefix}.{k}" if prefix else k)
    else:
        yield prefix, obj


def nutrient(n, en_map, source):
    return {"name": n["name"], "name_en": en_map.get(n["name"]), "amount": n["amount"], "unit": n["unit"],
            "percent_nrv": None, "source": source}


def bilingual_or_none(x):
    if isinstance(x, dict) and x.get("it") and x.get("en"):
        return {"it": x["it"], "en": x["en"]}
    return None


def null_item_skeleton():
    zone = {"sowing_or_transplant_months": None, "harvest_months": None, "seedbed_sowing_months": None,
            "direct_sowing_months": None, "transplant_months": None, "cultivation_notes": None}
    return {
        "italian_varieties_and_territories": {"notable_varieties": None, "has_dop_igp": None, "dop_igp_labels": None,
                                              "eambrosia_verified": None},
        "images": {"primary": None, "gallery": [], "image_details": []},
        "seasonality": {"eufic_climatic_zones": {z: None for z in ZONES}, "eufic_by_country": {},
                        "italy_macro_areas": {"nord": None, "centro": None, "sud_isole": None},
                        "italy_national": None, "derivation_notes": None},
        "agricultural_calendar_italy": {"nord": dict(zone), "centro": dict(zone), "sud_isole": dict(zone),
                                        "agronomic_params": None, "cultivation_notes": None},
        "buying_guide": {"shopping_list_preview": None, "detailed_selection": None},
        "ripening_and_storage": {
            "ripening_type": None, "ripening_badge_label": None, "card_short_storage": None, "primary_location": None,
            "storage_instructions": None,
            "postharvest_physiology": {"optimal_temperature_c": None, "optimal_humidity_percent": None,
                                       "respiration_rate_class": None, "freezing_point_c": None,
                                       "chilling_injury": {"susceptible": None, "critical_temperature_c": None, "symptoms": None},
                                       "estimated_shelf_life_days": {"room_temp_days": None, "refrigerated_days": None,
                                                                     "in_freezer_months": None}},
            "ripening_management": {"slow_down": None, "speed_up": None},
            "ethylene_compatibility": {"produces_ethylene": None, "ethylene_production_class": None,
                                       "sensitive_to_ethylene": None, "keep_away_from": [], "compatibility_notes": None}},
        "nutrition_and_sustainability": {
            "data_basis": None, "edible_portion_percentage": None, "water_percentage": None, "kcal_per_100g": None,
            "kj_per_100g": None,
            "macros_per_100g": {"carbs_g": None, "sugars_g": None, "starch_g": None, "proteins_g": None, "fats_g": None,
                                "fiber_g": None, "salt_g": None},
            "vitamins": [], "minerals": [], "bioactive_compounds": [], "nutrition_claims_eu": None,
            "health_benefits_and_curiosities": None, "culinary_waste_reduction": None},
    }


def sources_block(ix, from_draft):
    s = ix["sources"]
    b = ix["botany_check"]
    local = []
    if s.get("odc_pdf_row"):
        local += ["fonti_locali/odc-tabella-nord.pdf", "fonti_locali/odc-tabella-centro.pdf", "fonti_locali/odc-tabella-sud.pdf"]
    if s.get("wwf_row"):
        local.append("fonti_locali/Calendario-della-Frutta-e-Verdura-di-Stagione.pdf")
    if s.get("greenpeace_name"):
        local.append("fonti_locali/calendario-frutta-e-verdura-di-stagione_greenpeace.pdf")
    if s.get("biosuisse_row"):
        local.append("fonti_locali/BioSuisse-calendariostagionale-2026-11-01.pdf")
    post = [u for u in [(s.get("uc_davis") or {}).get("url"), s["usda_hb66"]["url"]] if u]
    bot = [u for u in [b["eppo"].get("url"), (b.get("wfo") or {}).get("url"), (b.get("gbif") or {}).get("url")] if u]
    return {
        "from_user_draft": from_draft,
        "local_files_used": local,
        "nutrition_crea_url": (s.get("crea") or {}).get("url"),
        "nutrition_bda_ieo_url": "https://bda.ieo.it/?page_id=87" if s.get("bda_ieo") else None,
        "postharvest_ucdavis_usda_url": post,
        "seasonality_and_storage_urls": [u for u in [s.get("altroconsumo_url"), s.get("my_personaltrainer_url"),
                                                     "https://www.my-personaltrainer.it/alimentazione/frutta-conservazione-stagionalita.html"] if u],
        "agricultural_calendar_urls": [u for u in [s.get("ortodacoltivare_url")] if u],
        "botany_eppo_wfo_url": bot,
        "eufic_url": "https://www.eufic.org/en/explore-seasonal-fruit-and-vegetables-in-europe" if s.get("eufic_keys") else None,
        "other_urls": [],
        "source_codes": {
            "crea": (s.get("crea") or {}).get("code"), "crea_match": (s.get("crea") or {}).get("match"),
            "bda_ieo": (s.get("bda_ieo") or {}).get("code"), "bda_ieo_match": (s.get("bda_ieo") or {}).get("match"),
            "uc_davis": (s.get("uc_davis") or {}).get("slug"), "uc_davis_match": (s.get("uc_davis") or {}).get("match"),
            "odc_pdf_row": s.get("odc_pdf_row"), "wwf_row": s.get("wwf_row"), "greenpeace_name": s.get("greenpeace_name"),
            "biosuisse_row": s.get("biosuisse_row"), "eufic_keys": s.get("eufic_keys", []),
        },
    }


def migrate_item(d, ix, legacy):
    """d = draft entry (or None for new ones), ix = index entry."""
    iid = ix["id"]
    item = {"id": iid, "names": {"it": ix["names"]["it"], "en": ix["names"]["en"], "synonyms": None}, "category": ix["category"]}
    eppo = ix["botany_check"]["eppo"]
    wfo = ix["botany_check"].get("wfo") or {}
    gbif = ix["botany_check"].get("gbif") or {}
    sk = null_item_skeleton()
    notes, lg = [], {}

    if d is None:
        cat = next(c for c in load_json(CONFIG / "catalog.json")["items"] if c["id"] == iid)
        item["botany"] = {"scientific_name": ix["scientific_name"], "eppo_code": eppo.get("eppo_code"),
                          "eppo_preferred_name": eppo.get("eppo_preferred_name"), "wfo_id": wfo.get("wfo_id"),
                          "gbif_key": gbif.get("gbif_key"), "family": wfo.get("family") or gbif.get("family"),
                          "genus": ix["scientific_name"].split()[0], "plant_part_used": cat["part"]}
        item.update(sk)
        item["sources_by_topic"] = sources_block(ix, False)
        notes.append("Alimento nuovo (non presente nella bozza), aggiunto dal catalogo multi-fonte: tutti i contenuti verranno compilati al Passo 1.3.")
    else:
        b = d["botany"]
        part = PLANT_PART.get(b["plant_part_used"], b["plant_part_used"])
        if part != b["plant_part_used"]:
            notes.append(f"plant_part_used '{b['plant_part_used']}' (bozza) normalizzato in '{part}'.")
        sci = ix["scientific_name"]
        if sci != b["scientific_name"]:
            notes.append(f"Nome scientifico cambiato: '{b['scientific_name']}' -> '{sci}'. {ix.get('override_reason') or ''}".strip())
            lg["botany.scientific_name"] = b["scientific_name"]
        family = b.get("family")
        if wfo.get("family") and family and wfo["family"] != family:
            notes.append(f"Famiglia: bozza '{family}', WFO '{wfo['family']}' (verificare classificazione APG IV al Passo 1.3).")
        item["botany"] = {"scientific_name": sci, "eppo_code": eppo.get("eppo_code"),
                          "eppo_preferred_name": eppo.get("eppo_preferred_name"), "wfo_id": wfo.get("wfo_id"),
                          "gbif_key": gbif.get("gbif_key"), "family": family, "genus": b.get("genus"), "plant_part_used": part}

        v = d["italian_varieties_and_territories"]
        item["italian_varieties_and_territories"] = {"notable_varieties": v.get("notable_varieties"),
                                                     "has_dop_igp": v.get("has_dop_igp"),
                                                     "dop_igp_labels": v.get("dop_igp_names") or [], "eambrosia_verified": False}
        # images: the draft's .png files do not exist on disk -> Commons candidates kept for Step 1.3
        lg["images.image_details"] = d["images"]["image_details"]
        item["images"] = {"primary": None, "gallery": [], "image_details": []}
        notes.append("Immagini: i file PNG indicati dalla bozza non esistono; i riferimenti Commons sono in draft_legacy_values.json come candidati per il download.")

        s = d["seasonality"]
        lg["seasonality.eufic_climatic_zones"] = s["eufic_climatic_zones"]
        item["seasonality"] = {"eufic_climatic_zones": {z: None for z in ZONES}, "eufic_by_country": {},
                               "italy_macro_areas": {k: s["italy_macro_areas"].get(k) for k in ("nord", "centro", "sud_isole")},
                               "italy_national": None, "derivation_notes": None}
        notes.append("Stagionalità EUFIC a 6 zone della bozza NON proveniente da EUFIC (che pubblica dati per Paese): rimossa e conservata in draft_legacy_values.json; verrà ricalcolata dai dati EUFIC reali.")

        a = d["agricultural_calendar_italy"]

        def zone(z):
            zz = a.get(z) or {}
            return {"sowing_or_transplant_months": zz.get("sowing_or_transplant_months"), "harvest_months": zz.get("harvest_months"),
                    "seedbed_sowing_months": None, "direct_sowing_months": None, "transplant_months": None,
                    "cultivation_notes": bilingual_or_none(zz.get("cultivation_notes"))}
        g = a.get("home_garden_params")
        item["agricultural_calendar_italy"] = {
            "nord": zone("nord"), "centro": zone("centro"), "sud_isole": zone("sud_isole"),
            "agronomic_params": None if g is None else {
                "sowing_depth_cm": g.get("sowing_depth_cm"), "plant_spacing_cm": g.get("plant_spacing_cm"),
                "sun_exposure": g.get("sun_exposure"), "lunar_phase_advice": g.get("lunar_phase_advice")},
            "cultivation_notes": None}

        item["buying_guide"] = {k: bilingual_or_none(d["buying_guide"].get(k)) for k in ("shopping_list_preview", "detailed_selection")}

        r = d["ripening_and_storage"]
        ci = r.get("chilling_injury") or {}
        sl = r.get("estimated_shelf_life_days") or {}
        e = r.get("ethylene_compatibility") or {}
        item["ripening_and_storage"] = {
            "ripening_type": r.get("ripening_type"), "ripening_badge_label": bilingual_or_none(r.get("ripening_badge_label")),
            "card_short_storage": bilingual_or_none(r.get("card_short_storage")), "primary_location": r.get("primary_location"),
            "storage_instructions": bilingual_or_none(r.get("storage_instructions")),
            "postharvest_physiology": {
                "optimal_temperature_c": r.get("optimal_temperature_c"), "optimal_humidity_percent": r.get("optimal_humidity_percent"),
                "respiration_rate_class": r.get("respiration_rate_class"), "freezing_point_c": None,
                "chilling_injury": {"susceptible": ci.get("susceptible"), "critical_temperature_c": ci.get("critical_temperature_c"),
                                    "symptoms": bilingual_or_none(ci.get("symptoms"))},
                "estimated_shelf_life_days": {"room_temp_days": sl.get("room_temp_days"), "refrigerated_days": sl.get("refrigerated_days"),
                                              "in_freezer_months": sl.get("in_freezer_months")}},
            "ripening_management": {k: bilingual_or_none((r.get("ripening_management") or {}).get(k)) for k in ("slow_down", "speed_up")},
            "ethylene_compatibility": {"produces_ethylene": e.get("produces_ethylene"), "ethylene_production_class": None,
                                       "sensitive_to_ethylene": e.get("sensitive_to_ethylene"),
                                       "keep_away_from": list(e.get("keep_away_from") or []),
                                       "compatibility_notes": bilingual_or_none(e.get("compatibility_notes"))}}

        n = d["nutrition_and_facts"]
        m = n.get("macros_per_100g") or {}
        vit, mins, bio = [], [], []
        for x in n.get("vitamins", []) + n.get("minerals", []):
            if x["name"] in VITAMINS_EN or x["name"] in FOLATE_NAMES:
                vit.append(nutrient(x, VITAMINS_EN, "user_draft"))
            elif x["name"] in MINERALS_EN:
                mins.append(nutrient(x, MINERALS_EN, "user_draft"))
            else:
                bio.append(nutrient(x, {}, "user_draft"))
        moved = [x["name"] for x in n.get("vitamins", []) if x["name"] not in VITAMINS_EN]
        if moved:
            notes.append("Voci della lista 'vitamine' della bozza riclassificate (minerali o composti bioattivi): " + ", ".join(moved) + ".")
        lg["nutrition_and_facts.nutrition_claims_eu"] = n.get("nutrition_claims_eu")
        item["nutrition_and_sustainability"] = {
            "data_basis": "bozza utente (valori compatibili con tabelle INRAN 2000, da verificare con CREA 2019 / BDA-IEO)",
            "edible_portion_percentage": n.get("edible_portion_percentage"), "water_percentage": m.get("water_g"),
            "kcal_per_100g": n.get("kcal_per_100g"), "kj_per_100g": None,
            "macros_per_100g": {"carbs_g": m.get("carbs_g"), "sugars_g": m.get("sugars_g"), "starch_g": None,
                                "proteins_g": m.get("proteins_g"), "fats_g": m.get("fats_g"), "fiber_g": m.get("fiber_g"), "salt_g": None},
            "vitamins": vit, "minerals": mins, "bioactive_compounds": bio,
            "nutrition_claims_eu": None,
            "health_benefits_and_curiosities": bilingual_or_none(n.get("health_benefits_and_curiosities")),
            "culinary_waste_reduction": bilingual_or_none(n.get("culinary_waste_reduction"))}
        notes.append("Claim nutrizionali della bozza rimossi (solo IT, molti non previsti dall'Allegato del Reg. CE 1924/2006, es. 'Aroma eccezionale', 'Energizzante'): conservati in draft_legacy_values.json, verranno ricalcolati da valori verificati.")

        lg["sources_by_topic"] = d.get("sources_by_topic")
        item["sources_by_topic"] = sources_block(ix, True)
        notes.append("URL della bozza sostituiti con URL verificati dall'indice (molti URL della bozza erano 404 o puntavano ad alimenti diversi); originali in draft_legacy_values.json.")

    # completezza
    body = {k: v for k, v in item.items() if k not in ("sources_by_topic",)}
    paths = list(leaf_paths(body))
    missing = sorted(p for p, v in paths if v is None)
    filled = sorted(p for p, v in paths if v is not None and v != [] and v != {} and p not in ("id", "category")
                    and not p.startswith(("names", "botany.eppo", "botany.wfo", "botany.gbif")))
    item["data_completeness"] = {
        "is_complete": False,
        "fields_from_initial_draft": filled if d is not None else [],
        "fields_pending_verification": filled if d is not None else [],
        "fields_enriched_via_scraping": [p for p in ("botany.eppo_code", "botany.eppo_preferred_name", "botany.wfo_id", "botany.gbif_key")
                                         if item["botany"].get(p.split(".")[1]) is not None],
        "missing_fields": missing,
        "discrepancies": [],
        "notes": " ".join(notes),
    }
    if lg:
        legacy[iid] = lg
    return item


def metadata(draft_md):
    leg = draft_md["seasonality_states_legend"]
    ui_en = {"primizie": "Early season", "in_season": "In season", "peak_season": "Peak season",
             "end_of_season": "End of season", "out_of_season": "Out of season", "not_applicable": "Not grown locally"}
    zmap = load_json(CONFIG / "eufic_zone_map.json")
    zones_names = {
        "mediterranean": ("Mediterranea", "Mediterranean"), "continental": ("Continentale", "Continental"),
        "atlantic": ("Atlantica", "Atlantic"), "boreal": ("Boreale", "Boreal"),
        "mountain": ("Alpina / montana", "Alpine / mountain"), "pannonian": ("Pannonica", "Pannonian")}
    zl = {}
    for z, (it, en) in zones_names.items():
        zl[z] = {"it": it, "en": en,
                 "countries_primary": sorted(c for c, v in zmap["countries"].items() if v["zone"] == z),
                 "countries_partial": sorted(c for c, v in zmap["countries"].items() if z in v.get("also", []))}
    zl["_method"] = {"it": "Dati EUFIC per Paese aggregati per zona usando la regione biogeografica EEA prevalente di ciascun Paese (vedi scripts/config/eufic_zone_map.json).",
                     "en": "EUFIC per-country data aggregated by zone using each country's dominant EEA biogeographical region (see scripts/config/eufic_zone_map.json).",
                     "reference": zmap["reference"]}
    return {
        "app_title": draft_md.get("app_title", "Peak Season"),
        "version": "2.0.0",
        "generated": datetime.date.today().isoformat(),
        "schema_version": "2.0",
        "sustainable_diet_summary": {
            "it": draft_md["sustainable_diet_scientific_references"]["it"],
            "en": draft_md["sustainable_diet_scientific_references"]["en"],
            "key_points": None,
            "source_url": "https://www.eufic.org/en/healthy-living/article/are-seasonal-fruit-and-vegetables-better-for-the-environment",
            "status": "from_user_draft_unverified"},
        "official_sources": load_json(CONFIG / "sources_registry.json")["sources"],
        "seasonality_states_legend": {k: {"it": v["it"], "en": v["en"], "color_hex": v["color_hex"],
                                          "ui_label": {"it": v.get("ui_label"), "en": ui_en[k]}} for k, v in leg.items()},
        "eufic_climatic_zones_legend": zl,
        "italy_macro_areas_legend": draft_md["italy_macro_areas_legend"],
        "generation_log": [{"step": "1.2 migrate_draft.py", "date": datetime.date.today().isoformat(),
                            "note": "Migrazione bozza v1.0.0 (2026-11-02) + 18 nuovi alimenti dal catalogo."}],
    }


def main():
    draft = load_json(DRAFT)
    by_id = {it["id"]: it for it in draft["items"]}
    index = load_json(DATA / "items_index.json")
    legacy = {}
    items = [migrate_item(by_id.get(ix.get("draft_id") or ix["id"]) if ix["present_in_draft"] else None, ix, legacy)
             for ix in index["items"]]
    ids = {i["id"] for i in items}
    for it in items:  # keep_away_from deve puntare a ID esistenti
        kaf = it["ripening_and_storage"]["ethylene_compatibility"]["keep_away_from"]
        bad = [k for k in kaf if k not in ids]
        if bad:
            it["ripening_and_storage"]["ethylene_compatibility"]["keep_away_from"] = [k for k in kaf if k in ids]
            it["data_completeness"]["notes"] += f" keep_away_from: rimossi ID inesistenti {bad}."
    db = {"metadata": metadata(draft["metadata"]), "items": items}
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", {
        "_doc": "Valori della bozza originale (v1.0.0, 2026-11-02) non riportati in database.json, con il motivo nelle note di ciascun alimento. La bozza completa è in data/_backup_bozza_2026-11-04/.",
        "items": legacy})
    n_missing = sum(len(i["data_completeness"]["missing_fields"]) for i in items)
    print(f"Migrated {len(items)} products ({sum(i['sources_by_topic']['from_user_draft'] for i in items)} from the draft). "
          f"Total null fields: {n_missing}. Legacy: {len(legacy)} products.")


if __name__ == "__main__":
    main()

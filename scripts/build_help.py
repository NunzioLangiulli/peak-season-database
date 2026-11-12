"""Sistema di aiuto dell'app (icona "?") e vocabolario bilingue dei codici.

Scrive nei metadati:
- metadata.vocabulary: per ogni campo a valori codificati, l'etichetta IT/EN di ogni codice (es. "climaterico" ->
  "Climaterico"/"Climacteric") e l'eventuale voce di glossario. Così l'app può essere tutta in italiano o tutta in inglese.
- metadata.glossary: le voci di spiegazione (scripts/config/glossary.json), con le fonti risolte dal registro.
- metadata.field_help: percorso del campo (relativo alla scheda) -> voci di glossario da aprire con il "?".
E in ogni scheda:
- help_refs: rimandi che dipendono dal contenuto dell'alimento (es. favismo per la fava, glutine per i cereali,
  climaterico per il pomodoro), con i campi in cui compaiono.
Uso:  python scripts/build_help.py   (dopo localize_fields.py)
"""
import re

from common import DATA, ROOT, finalize_completeness, load_json, save_json

L = lambda it, en: {"it": it, "en": en}  # noqa: E731
VOCAB = {
    "category": {"_glossary": None, "verdura": L("Verdura", "Vegetables"), "frutta": L("Frutta", "Fruit"),
                 "erbe_spezie": L("Erbe e spezie", "Herbs and spices"), "funghi": L("Funghi", "Mushrooms"), "cereali": L("Cereali", "Grains")},
    "botany.plant_part_used": {"_glossary": "scientific_name", "frutto": L("Frutto", "Fruit"), "foglia": L("Foglia", "Leaf"), "radice": L("Radice", "Root"),
                               "tubero": L("Tubero", "Tuber"), "infiorescenza_bocciolo": L("Infiorescenza o bocciolo", "Flower head or bud"),
                               "bulbo": L("Bulbo", "Bulb"), "fusto_costa": L("Fusto o costa", "Stem or stalk"), "seme": L("Seme", "Seed"),
                               "fiore": L("Fiore", "Flower"), "fungo_carpoforo": L("Corpo fruttifero del fungo", "Mushroom fruiting body")},
    "seasonality.state": {"_glossary": "seasonality_states", "primizie": L("Primizia", "Early season"), "in_season": L("Di stagione", "In season"),
                          "peak_season": L("Piena stagione", "Peak season"), "end_of_season": L("Fine stagione", "End of season"),
                          "out_of_season": L("Fuori stagione", "Out of season"), "not_applicable": L("Non coltivato nella zona", "Not grown in the area")},
    "seasonality.italy_macro_areas": {"_glossary": "italy_macro_areas", "nord": L("Nord", "North"), "centro": L("Centro", "Centre"), "sud_isole": L("Sud e Isole", "South and Islands")},
    "seasonality.eufic_climatic_zones": {"_glossary": "eufic_zones", "mediterranean": L("Mediterranea", "Mediterranean"), "continental": L("Continentale", "Continental"),
                                         "atlantic": L("Atlantica", "Atlantic"), "boreal": L("Boreale", "Boreal"), "mountain": L("Alpina", "Alpine"),
                                         "pannonian": L("Pannonica", "Pannonian")},
    "seasonality.estimates": {"_glossary": "seasonality_estimate",
                              "estimate": {**L("Stima dalla zona vicina", "Estimate from neighbouring zone"), "marker": "≈"},
                              "not_grown": L("Non coltivato qui", "Not grown here"), "unknown": L("Dato non disponibile", "No data available")},
    "seasonality.estimates.from": {"_glossary": "seasonality_estimate", "mediterranean": L("zona mediterranea", "Mediterranean zone"),
                                   "continental": L("zona continentale", "Continental zone"), "atlantic": L("zona atlantica", "Atlantic zone"),
                                   "boreal": L("zona boreale", "Boreal zone"), "mountain": L("zona alpina", "Alpine zone"), "pannonian": L("zona pannonica", "Pannonian zone"),
                                   "italy_nord": L("Nord Italia", "Northern Italy"), "italy_sud_isole": L("Sud e Isole", "Southern Italy and Islands")},
    "month": {"_glossary": None, **{str(i + 1): L(a, b) for i, (a, b) in enumerate(zip(
        ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"],
        ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]))}},
    "ripening_and_storage.ripening_type": {"_glossary": None, "climaterico": {**L("Climaterico", "Climacteric"), "glossary": "climacteric"},
                                           "non_climaterico": {**L("Non climaterico", "Non-climacteric"), "glossary": "non_climacteric"}},
    "ripening_and_storage.primary_location": {"_glossary": "home_storage", "frigorifero": L("Frigorifero", "Fridge"),
                                              "temperatura_ambiente": L("Temperatura ambiente", "Room temperature"), "luogo_fresco_buio": L("Luogo fresco e buio", "Cool, dark place")},
    "class_scale": {"_glossary": "respiration_rate", "_used_by": ["ripening_and_storage.postharvest_physiology.respiration_rate_class", "ripening_and_storage.ethylene_compatibility.ethylene_production_class"],
                    "very_low": L("Molto bassa", "Very low"), "low": L("Bassa", "Low"), "moderate": L("Moderata", "Moderate"), "high": L("Alta", "High"),
                    "very_high": L("Molto alta", "Very high"), "extremely_high": L("Elevatissima", "Extremely high")},
    "ripening_and_storage.postharvest_physiology.freezing_susceptibility": {"_glossary": "freezing_susceptibility", "most": L("Molto sensibile al gelo", "Most susceptible"),
                                                                           "moderate": L("Moderatamente sensibile", "Moderately susceptible"), "least": L("Poco sensibile", "Least susceptible")},
    "ripening_and_storage.home_storage.location": {"_glossary": "home_storage", "fridge": L("In frigorifero", "In the fridge"),
                                                   "counter_then_fridge": L("Fuori dal frigo finché matura, poi in frigo", "On the counter until ripe, then in the fridge"),
                                                   "room_temperature": L("A temperatura ambiente", "At room temperature"), "cool_dry_pantry": L("In dispensa, al fresco e all'asciutto", "In a cool, dry pantry")},
    "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days.room_temp_mode": {"_glossary": "shelf_life_home", "days": L("Giorni in dispensa", "Days in the pantry"),
                                                                                            "until_ripe": L("Fino a maturazione", "Until ripe"), "fridge_only": L("Solo frigorifero", "Fridge only")},
    "ripening_and_storage.storage_compatibility.group": {"_glossary": "storage_compatibility", "1A": L("Verdure da frigo (0-2 °C, umidità alta)", "Cold vegetables (0-2 °C, high humidity)"),
                                                         "1B": L("Frutta da frigo (0-2 °C)", "Cold fruit (0-2 °C)"), "2": L("Fresco, non freddo (7-10 °C)", "Cool, not cold (7-10 °C)"),
                                                         "3": L("Ambiente fresco (13-18 °C)", "Cool room (13-18 °C)")},
    "agricultural_calendar_italy.agronomic_params.sun_exposure": {"_glossary": "agronomic_params", "molto_soleggiato": L("Pieno sole", "Full sun"),
                                                                  "soleggiato": L("Soleggiato", "Sunny"), "anche_mezzombra": L("Anche mezz'ombra", "Also partial shade")},
    "agricultural_calendar_italy.agronomic_params.lunar_phase_advice": {"_glossary": "agronomic_params", "fase_crescente": L("Luna crescente (tradizione)", "Waxing moon (tradition)"),
                                                                        "fase_calante": L("Luna calante (tradizione)", "Waning moon (tradition)"), "indifferente": L("Indifferente", "Not relevant")},
    "images.image_details.view_type": {"_glossary": None, "full_frame": L("Prodotto a tutto campo", "Full frame"), "isolated_background": L("Su sfondo", "On plain background"),
                                       "plant_in_field": L("Pianta", "Plant"), "botanical_plate": L("Tavola botanica", "Botanical plate"),
                                       "cut_section": L("In sezione", "Cut"), "other": L("Altro", "Other")},
    "botany.upov_register": {"_glossary": "upov_variety_register", "VEG": L("Specie ortive", "Vegetable species"), "AGR": L("Specie agricole", "Agricultural species"), "FRU": L("Specie da frutto", "Fruit species")},
    "nutrition_and_sustainability.bioactive_compounds.group": {"_glossary": "polyphenols", "carotenoidi": L("Carotenoidi", "Carotenoids"), "flavonoidi": L("Flavonoidi", "Flavonoids"),
                                                               "acidi_fenolici": L("Acidi fenolici", "Phenolic acids"), "altri_polifenoli": L("Altri polifenoli", "Other polyphenols"),
                                                               "polifenoli_totali": L("Polifenoli totali", "Total polyphenols")},
    "sustainability_level": {"_glossary": "carbon_footprint", "_used_by": ["nutrition_and_sustainability.environmental_footprint.sustainability_rating.carbon_level",
                                                                          "nutrition_and_sustainability.environmental_footprint.sustainability_rating.water_level"],
                             "low": L("Bassa", "Low"), "medium": L("Media", "Medium"), "high": L("Alta", "High")},
    "match": {"_glossary": "data_quality", "_used_by": ["*.match", "botany.upov_match"], "exact": L("Esatto", "Exact"), "approx": L("Approssimato", "Approximate")},
    "nutrition_and_sustainability.allergens_eu.annex_ii_number": {"_glossary": "allergens", **{str(k): L(a, b) for k, (a, b) in {
        1: ("Cereali contenenti glutine", "Cereals containing gluten"), 2: ("Crostacei", "Crustaceans"), 3: ("Uova", "Eggs"), 4: ("Pesce", "Fish"),
        5: ("Arachidi", "Peanuts"), 6: ("Soia", "Soybeans"), 7: ("Latte", "Milk"), 8: ("Frutta a guscio", "Tree nuts"), 9: ("Sedano", "Celery"),
        10: ("Senape", "Mustard"), 11: ("Semi di sesamo", "Sesame seeds"), 12: ("Anidride solforosa e solfiti", "Sulphur dioxide and sulphites"),
        13: ("Lupini", "Lupin"), 14: ("Molluschi", "Molluscs")}.items()}},
}
FIELD_HELP = {
    "ripening_and_storage.ripening_type": ["climacteric", "non_climacteric"],
    "ripening_and_storage.ripening_badge_label": ["climacteric", "non_climacteric"],
    "ripening_and_storage.home_storage": ["home_storage"],
    "ripening_and_storage.card_short_storage": ["home_storage", "shelf_life_home"],
    "ripening_and_storage.perishability": ["perishability", "respiration_rate"],
    "ripening_and_storage.storage_compatibility": ["storage_compatibility"],
    "ripening_and_storage.postharvest_physiology.optimal_temperature_c": ["optimal_storage"],
    "ripening_and_storage.postharvest_physiology.optimal_humidity_percent": ["optimal_storage"],
    "ripening_and_storage.postharvest_physiology.respiration_rate_class": ["respiration_rate", "q10"],
    "ripening_and_storage.postharvest_physiology.freezing_point_c": ["freezing_point"],
    "ripening_and_storage.postharvest_physiology.freezing_susceptibility": ["freezing_susceptibility"],
    "ripening_and_storage.postharvest_physiology.chilling_injury": ["chilling_injury", "lowest_safe_temperature"],
    "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days": ["shelf_life_home", "optimal_storage"],
    "ripening_and_storage.ethylene_compatibility": ["ethylene", "ethylene_production", "ethylene_sensitivity"],
    "ripening_and_storage.ethylene_compatibility.keep_away_from": ["keep_away_from"],
    "seasonality.italy_macro_areas": ["seasonality_states", "italy_macro_areas"],
    "seasonality.eufic_climatic_zones": ["eufic_zones", "seasonality_states"],
    "seasonality.estimates": ["seasonality_estimate", "eufic_zones", "italy_macro_areas"],
    "agricultural_calendar_italy": ["sowing_transplant"],
    "agricultural_calendar_italy.agronomic_params": ["agronomic_params"],
    "nutrition_and_sustainability.edible_portion_percentage": ["edible_portion"],
    "nutrition_and_sustainability.vitamins": ["nrv"],
    "nutrition_and_sustainability.minerals": ["nrv"],
    "nutrition_and_sustainability.nutrition_claims_eu": ["nutrition_claims", "nrv"],
    "nutrition_and_sustainability.protein_reference": ["larn"],
    "nutrition_and_sustainability.reference_portion": ["reference_portion"],
    "nutrition_and_sustainability.allergens_eu": ["allergens"],
    "nutrition_and_sustainability.bioactive_compounds": ["carotenoids", "flavonoids", "polyphenols"],
    "nutrition_and_sustainability.environmental_footprint": ["carbon_footprint", "water_footprint", "greenhouse"],
    "nutrition_and_sustainability.traditional_products_pat": ["pat"],
    "italian_varieties_and_territories.notable_varieties": ["varieties"],
    "italian_varieties_and_territories.dop_igp_labels": ["dop_igp"],
    "botany.scientific_name": ["scientific_name"],
    "botany.upov_code": ["upov_variety_register"],
    "botany.varieties_registered_italy": ["upov_variety_register"],
}
TEXT_FIELDS = ["buying_guide.shopping_list_preview", "buying_guide.detailed_selection", "ripening_and_storage.storage_instructions",
               "ripening_and_storage.postharvest_physiology.chilling_injury.symptoms", "nutrition_and_sustainability.health_benefits_and_curiosities",
               "nutrition_and_sustainability.culinary_waste_reduction", "ripening_and_storage.ethylene_compatibility.compatibility_notes"]


def get(o, path):
    for k in path.split("."):
        o = o.get(k) if isinstance(o, dict) else None
    return o


def main():
    db = load_json(DATA / "database.json")
    gl = load_json(ROOT / "scripts" / "config" / "glossary.json")["entries"]
    src = {s["key"]: s for s in db["metadata"]["official_sources"]}
    ids = {e["id"] for e in gl}
    for e in gl:
        for s in e["sources"]:
            if s not in src:
                print("  W fonte non registrata nel glossario:", e["id"], s)
        for x in e.get("see_also", []):
            if x not in ids:
                print("  W see_also inesistente:", e["id"], x)
    for f, v in FIELD_HELP.items():
        for g in v:
            if g not in ids:
                print("  W field_help verso voce inesistente:", f, g)
    m = db["metadata"]
    m["glossary"] = {e["id"]: {"term": e["term"], "short": e["short"], "text": e["text"],
                               "sources": [{"key": s, "name": src.get(s, {}).get("name"), "url": src.get(s, {}).get("url")} for s in e["sources"]],
                               "see_also": e.get("see_also", [])} for e in gl}
    m["vocabulary"] = VOCAB
    m["field_help"] = FIELD_HELP
    leg = m.get("seasonality_states_legend", {})
    if "peak_season" in leg:   # testo della bozza ("massima qualita' nutrizionale") non supportato dalle fonti
        leg["peak_season"]["it"] = "Piena stagione (mesi centrali di un periodo in cui tutte le fonti concordano)"
        leg["peak_season"]["en"] = "Peak season (central months of a period on which all sources agree)"
    m["postharvest_method"]["en"] = (
        "(Kader A.A., Postharvest Technology of Horticultural Crops, UC ANR 2002, used by UC Davis):\n"
        "- respiration at 5 °C (mg CO2/kg·h): <5 very_low, 5-10 low, 10-20 moderate, 20-40 high, 40-60 very_high, >60 extremely_high\n"
        "- ethylene at 20 °C (µL/kg·h): <0.1 very_low, 0.1-1 low, 1-10 moderate, 10-100 high, >100 very_high\n"
        "keep_away_from = database foods with high/very_high ethylene production, for sensitive foods.")
    m["protein_reference_method"]["en"] = (
        "Protein reference for Italy (nutrition_and_sustainability.protein_reference).\n\n"
        "National scientific reference: LARN - SINU, 4th revision 2014: adults 18-64 years PRI 0.90 g/kg/day -> 63 g/day men (70 kg), "
        "54 g/day women (60 kg); 65 years and over PRI 1.1 g/kg/day -> 77 g/day men, 66 g/day women.\n"
        "EU labelling reference: protein RI 50 g/day (Reg. (EU) 1169/2011, Annex XIII, part B).\n"
        "Claims (Reg. (EC) 1924/2006): \"source of / high in protein\" = >=12% / >=20% of energy from protein. The criterion is legal but "
        "relative: in very low-calorie vegetables it is met even with a few grams. If 100 g cover less than 10% of the LARN PRI "
        "(adult woman, 5.4 g), the claim stays (it is compliant) but comes with a note putting it in context.")
    for key in ("perishability_legend", "home_storage_legend", "storage_compatibility_legend"):
        b = m.get(key, {}).get("basis")
        if isinstance(b, str):
            m[key]["basis"] = {"it": b, "en": {
                "perishability_legend": "Respiration class at 5 °C according to Kader (USDA HB66, Respiratory Metabolism, Table 1): storage life varies inversely with respiration.",
                "home_storage_legend": "UC Davis/Kader guide \"Storing Fresh Fruits and Vegetables for Better Taste\" + USDA FoodKeeper",
                "storage_compatibility_legend": "USDA HB66, Table 1 (Thompson et al. 1996): produce that can be stored together for 7 days; ethylene < 1 ppm."}[key]}
    kw = [(e["id"], re.compile("|".join(re.escape(k) for k in e["keywords"]), re.I)) for e in gl if e.get("keywords")]
    n_refs = 0
    for it in db["items"]:
        refs = {}

        def add(g, field):
            refs.setdefault(g, set()).add(field)
        rt = it["ripening_and_storage"].get("ripening_type")
        if rt:
            add("climacteric" if rt == "climaterico" else "non_climacteric", "ripening_and_storage.ripening_type")
        if it["ripening_and_storage"]["postharvest_physiology"]["chilling_injury"].get("susceptible"):
            add("chilling_injury", "ripening_and_storage.postharvest_physiology.chilling_injury")
        n = it["nutrition_and_sustainability"]
        for a in n.get("allergens_eu") or []:
            add("allergens", "nutrition_and_sustainability.allergens_eu")
            if a["annex_ii_number"] == 1:
                add("gluten", "nutrition_and_sustainability.allergens_eu")
        if it["italian_varieties_and_territories"].get("dop_igp_labels"):
            add("dop_igp", "italian_varieties_and_territories.dop_igp_labels")
        if any(s["source_key"] == "slow_food" for v in it["italian_varieties_and_territories"].get("varieties_verification") or [] for s in v["sources"]):
            add("slow_food", "italian_varieties_and_territories.notable_varieties")
        if (n.get("traditional_products_pat") or {}).get("count"):
            add("pat", "nutrition_and_sustainability.traditional_products_pat")
        pb = (it["ripening_and_storage"].get("perishability") or {}).get("basis") or {}
        if "Q10" in (pb.get("it") or ""):
            add("q10", "ripening_and_storage.perishability")
        ef = n.get("environmental_footprint") or {}
        if ef.get("greenhouse_comparison"):
            add("greenhouse", "nutrition_and_sustainability.environmental_footprint.greenhouse_comparison")
        for f in TEXT_FIELDS:
            t = get(it, f)
            txt = " ".join(t.values()) if isinstance(t, dict) else ""
            for gid, rx in kw:
                if rx.search(txt):
                    add(gid, f)
        it["help_refs"] = [{"glossary_id": g, "fields": sorted(fs)} for g, fs in sorted(refs.items())]
        n_refs += len(refs)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(f"glossario: {len(gl)} voci; vocabolario: {len(VOCAB)} campi; field_help: {len(FIELD_HELP)}; rimandi negli alimenti: {n_refs}")


if __name__ == "__main__":
    main()

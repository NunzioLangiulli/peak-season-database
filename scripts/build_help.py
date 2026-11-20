"""App help system ("?" icon) and bilingual vocabulary of the codes.

Writes to the metadata:
- metadata.vocabulary: for every field with coded values, the IT/EN label of each code (e.g. "climaterico" ->
  "Climaterico"/"Climacteric") and the glossary entry if any. This way the app can be entirely in Italian or entirely in English.
- metadata.glossary: the explanation entries (scripts/config/glossary.json), with sources resolved from the register.
- metadata.field_help: field path (relative to the record) -> glossary entries to open with the "?".
And in every record:
- help_refs: references depending on the product's content (e.g. favism for broad beans, gluten for cereals,
  climacteric for tomato), with the fields where they appear.
Usage:  python scripts/build_help.py   (after localize_fields.py)
"""
import re

from common import DATA, ROOT, finalize_completeness, load_json, save_json

# labels of the coded values: scripts/config/vocabulary.json (edited with the Admin Studio, Vocabulary tab)
VOCAB = load_json(ROOT / "scripts" / "config" / "vocabulary.json")["vocabulary"]
# products whose carbohydrates need their own explanation under the macros (macros_per_100g.carbs_note = glossary id):
# black salsify's available carbohydrates include ~5 g that are neither starch nor sugars, most likely inulin; the USDA
# products' carbohydrates are "by difference" minus fibre, so they exceed starch + sugars (organic acids and the like)
CARBS_NOTE = {"scorzonera_black_salsify": "inulin", "navone_swede": "carbs_by_difference", "gombo_okra": "carbs_by_difference",
              "mirtillo_rosso_lingonberry": "carbs_by_difference", "cardoncello_king_oyster_mushroom": "carbs_by_difference"}
FIELD_HELP = {
    "ripening_and_storage.ripening_type": ["climacteric", "non_climacteric"],
    "ripening_and_storage.ripening_badge_label": ["climacteric", "non_climacteric"],
    "ripening_and_storage.home_storage": ["home_storage"],
    "ripening_and_storage.card_short_storage": ["home_storage", "shelf_life_home"],
    "ripening_and_storage.perishability": ["perishability"],
    "ripening_and_storage.storage_compatibility": ["storage_compatibility"],
    "ripening_and_storage.postharvest_physiology.optimal_temperature_c": ["optimal_storage"],
    "ripening_and_storage.postharvest_physiology.optimal_humidity_percent": ["optimal_storage"],
    "ripening_and_storage.postharvest_physiology.respiration_rate_class": ["perishability"],
    "ripening_and_storage.postharvest_physiology.freezing_point_c": ["freezing_point"],
    "ripening_and_storage.postharvest_physiology.freezing_susceptibility": ["freezing_susceptibility"],
    "ripening_and_storage.postharvest_physiology.chilling_injury": ["chilling_injury", "lowest_safe_temperature"],
    "ripening_and_storage.postharvest_physiology.estimated_shelf_life_days": ["shelf_life_home", "optimal_storage"],
    "ripening_and_storage.ethylene_compatibility": ["ethylene"],
    "ripening_and_storage.ethylene_compatibility.ethylene_production_class": ["ethylene"],
    "ripening_and_storage.ethylene_compatibility.sensitive_to_ethylene": ["ethylene"],
    "ripening_and_storage.ethylene_compatibility.keep_away_from": ["keep_away_from"],
    "seasonality.italy_macro_areas": ["seasonality_states", "italy_macro_areas"],
    "seasonality.eufic_climatic_zones": ["eufic_zones", "seasonality_states"],
    "seasonality.estimates": ["seasonality_estimate", "eufic_zones", "italy_macro_areas"],
    "agricultural_calendar_italy": ["sowing_transplant"],
    "nutrition_and_sustainability.edible_portion_percentage": ["edible_portion"],
    "nutrition_and_sustainability.macros_per_100g.carbs_g": ["available_carbohydrates"],
    "nutrition_and_sustainability.vitamins": ["nrv"],
    "nutrition_and_sustainability.minerals": ["nrv"],
    "nutrition_and_sustainability.nutrition_claims_eu": ["nutrition_claims"],
    "nutrition_and_sustainability.protein_reference": ["larn"],
    "nutrition_and_sustainability.reference_portion": ["reference_portion"],
    "nutrition_and_sustainability.allergens_eu": ["allergens"],
    "nutrition_and_sustainability.bioactive_compounds": ["carotenoids", "flavonoids", "polyphenols"],
    "nutrition_and_sustainability.environmental_footprint": ["carbon_footprint", "water_footprint", "greenhouse"],
    "nutrition_and_sustainability.traditional_products_pat": ["pat"],
    "italian_varieties_and_territories.notable_varieties": ["varieties"],
    "italian_varieties_and_territories.dop_igp_labels": ["dop_igp"],
    "botany.scientific_name": ["scientific_name"],
    "botany.upov_code": ["scientific_name"],
    "botany.varieties_registered_italy": ["scientific_name"],
    "botany.eppo_code": ["scientific_name"],
    "sources_by_topic.useful_links": ["useful_links"],
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
                print("  W source not registered in the glossary:", e["id"], s)
        for x in e.get("see_also", []):
            if x not in ids:
                print("  W non-existent see_also:", e["id"], x)
    for f, v in FIELD_HELP.items():
        for g in v:
            if g not in ids:
                print("  W field_help pointing to a non-existent entry:", f, g)
    m = db["metadata"]
    m["glossary"] = {e["id"]: {"term": e["term"], "short": e["short"], "text": e["text"],
                               "sources": [{"key": s, "name": src.get(s, {}).get("name"), "url": src.get(s, {}).get("url")} for s in e["sources"]],
                               "see_also": e.get("see_also", []),
                               # optional very short line shown on the product page before the "?" (the app falls back to short)
                               **({"footnote": e["footnote"]} if e.get("footnote") else {})} for e in gl}
    # groups written by later scripts (botany.family by build_app_support_metadata.py) are kept, so the order of reruns
    # does not matter
    kept = {k: v for k, v in (m.get("vocabulary") or {}).items() if k not in VOCAB and k in ("botany.family",)}
    m["vocabulary"] = {**VOCAB, **kept}
    m["field_help"] = FIELD_HELP
    leg = m.get("seasonality_states_legend", {})
    if "peak_season" in leg:   # draft text ("maximum nutritional quality") not supported by the sources
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
    # keywords match at the start of a word; all-caps acronyms (DOP, IGP, G6PD) only as whole, upper-case words
    # (otherwise "dopo" would match DOP)
    kw = [(e["id"], re.compile("|".join((r"(?-i:\b" + re.escape(k) + r"\b)") if k.isupper() else (r"\b" + re.escape(k))
                                         for k in e["keywords"]), re.I)) for e in gl if e.get("keywords")]
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
            add("perishability", "ripening_and_storage.perishability")
        ef = n.get("environmental_footprint") or {}
        rating = ef.get("sustainability_rating") or {}
        if rating:                                   # what the sustainability tip talks about (the app picks its icon/help from it)
            tips = (rating.get("tips") or {}).get("it") or ""
            if "in serra" in tips.lower():           # tip about heated or unheated greenhouses
                rating["tips_topic"] = "greenhouse"
            else:
                rating.pop("tips_topic", None)
        if ef.get("greenhouse_comparison"):
            add("greenhouse", "nutrition_and_sustainability.environmental_footprint.greenhouse_comparison")
        mac = n.get("macros_per_100g") or {}
        if it["id"] in CARBS_NOTE:
            mac["carbs_note"] = CARBS_NOTE[it["id"]]
            add(CARBS_NOTE[it["id"]], "nutrition_and_sustainability.macros_per_100g.carbs_g")
        else:
            mac.pop("carbs_note", None)
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
    print(f"glossary: {len(gl)} entries; vocabulary: {len(VOCAB)} fields; field_help: {len(FIELD_HELP)}; references in products: {n_refs}")


if __name__ == "__main__":
    main()

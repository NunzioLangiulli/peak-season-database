"""Adds products chosen by the project owner as exceptions to the inclusion rule (2026-11-05). Idempotent.

White truffle (Tuber magnatum): a very important Italian product with no CREA or BDA-IEO composition record
(the tables only have black truffle). The owner decided to include it anyway: nutrition stays empty and
declared as a gap. Data used, all from sources:
- botany: EPPO TUERMA (IT/EN names), GBIF 5258456;
- seasonality: Law 752/1985 art. 6 (enrich_special_seasonality.py); EUFIC "truffle (white)";
- postharvest: USDA HB66, Truffle chapter (pp. 588-589), which explicitly covers Tuber magnatum together with
  T. melanosporum: 0 °C, 90-95% RH, 20-30 days; not chill-sensitive; very low ethylene; respiration
  24-45 mg CO2/kg·h at 5 °C (same class as black truffle);
- home storage: FoodKeeper (mushrooms/truffles entry, as for black truffle);
- portion: IEO SmartFood "herbs and spices" group, as for black truffle;
- PAT: MASAF list (enrich_pat.py, keywords in config/pat_keywords.json).
The record starts from the black truffle one: species-specific fields are replaced or cleared.
Usage:  python scripts/add_items.py   (then enrich_special_seasonality, enrich_pat, apply_texts, build_source_registry…)
"""
import copy

from common import CONFIG, DATA, RAW, finalize_completeness, load_json, save_json
from enrich_seasonality import ZONES, eufic_country_table, states

NEW = {
    "id": "tartufo_bianco_white_truffle", "from": "tartufo_nero_black_truffle",
    "names": {"it": "Tartufo bianco", "en": "White truffle",
              "synonyms": {"it": ["tartufo bianco pregiato", "tartufo di Alba", "tartufo del Piemonte"], "en": ["Italian white truffle", "Alba truffle"]}},
    "botany": {"scientific_name": "Tuber magnatum", "eppo_code": "TUERMA", "eppo_preferred_name": "Tuber magnatum", "gbif_key": 5258456},
    "eufic_keys": ["truffle (white)"],
}
NUTR_NOTE = ("Nessuna scheda di composizione per il tartufo bianco in CREA né in BDA-IEO (le tabelle riportano solo il tartufo nero): valori nutrizionali non disponibili da fonti ufficiali. Alimento incluso su decisione dell'utente.",
             "No composition data for white truffle in CREA or BDA-IEO (the tables only cover black truffle): nutrition values not available from official sources. Food included at the user's request.")


def build(db):
    I = {i["id"]: i for i in db["items"]}
    if NEW["id"] in I:
        return None
    it = copy.deepcopy(I[NEW["from"]])
    it["id"] = NEW["id"]
    it["names"] = NEW["names"]
    it["botany"].update(NEW["botany"])
    it["images"] = {"primary": None, "gallery": [], "image_details": []}
    # European seasonality (EUFIC)
    eufic = load_json(RAW / "eufic_fvlist.json")
    zmap = load_json(CONFIG / "eufic_zone_map.json")["countries"]
    fresh, stored = eufic_country_table(NEW["eufic_keys"], eufic)
    s = it["seasonality"]
    s["eufic_by_country"] = {c: fresh.get(c, [False] * 12) for c in sorted(set(fresh) | set(stored))}
    for z in ZONES:
        cs = [c for c, v in zmap.items() if v["zone"] == z and (c in fresh or c in stored)]
        sc = [sum(fresh.get(c, [False] * 12)[m] for c in cs) / len(cs) for m in range(12)] if cs else None
        s["eufic_climatic_zones"][z] = states(sc, [None] * 12, 2 if len(cs) >= 2 else 1) if cs else None
    s["eufic_zone_sources"] = {z: {"source": "eufic_map", "url": "https://www.eufic.org/en/explore-seasonal-fruit-and-vegetables-in-europe"}
                               for z, v in s["eufic_climatic_zones"].items() if v}
    # nutrizione: nessuna fonte
    n = it["nutrition_and_sustainability"]
    n["data_basis"] = {"it": NUTR_NOTE[0], "en": NUTR_NOTE[1]}
    for k in ("edible_portion_percentage", "water_percentage", "kcal_per_100g", "kj_per_100g"):
        n[k] = None
    n["macros_per_100g"] = {k: None for k in n["macros_per_100g"]}
    n["vitamins"], n["minerals"], n["bioactive_compounds"] = [], [], []
    n["nutrition_claims_eu"] = {"it": [], "en": []}
    n["protein_reference"] = None
    n["traditional_products_pat"] = None
    # traceability
    sb = it["sources_by_topic"]
    sb.update({"nutrition_crea_url": None, "nutrition_bda_ieo_url": None,
               "botany_eppo_wfo_url": ["https://gd.eppo.int/taxon/TUERMA", "https://www.gbif.org/species/5258456"]})
    sb["source_codes"].update({"crea": None, "crea_match": None, "bda_ieo": None, "bda_ieo_match": None, "eufic_keys": NEW["eufic_keys"]})
    sb["sources_used"] = []
    dc = it["data_completeness"]
    dc.update({"discrepancies": [], "fields_pending_verification": [],
               "fields_enriched_via_scraping": ["names", "botany", "seasonality.eufic_by_country", "seasonality.eufic_climatic_zones", "ripening_and_storage"],
               "notes": "Alimento aggiunto il 2026-11-05 su decisione dell'utente, in deroga alla regola di ammissione (manca la scheda CREA/BDA). "
                        "Botanica: EPPO TUERMA, GBIF 5258456. Post-raccolta: USDA HB66, capitolo Truffle (tratta T. magnatum e T. melanosporum insieme). "
                        "Stagionalità: Legge 752/1985 art. 6. Nutrizione non disponibile da fonti ufficiali."})
    na = set(dc.get("not_applicable_fields", []))
    na -= {p for p in na if p.startswith("nutrition_and_sustainability.protein_reference")}
    dc["not_applicable_fields"] = sorted(na)
    it.pop("help_refs", None)
    pos = db["items"].index(I[NEW["from"]]) + 1
    db["items"].insert(pos, it)
    finalize_completeness(it)
    return it


def index_entry():
    idx = load_json(DATA / "items_index.json")
    if any(x["id"] == NEW["id"] for x in idx["items"]):
        return
    base = copy.deepcopy(next(x for x in idx["items"] if x["id"] == NEW["from"]))
    base.update({"id": NEW["id"], "names": {"it": NEW["names"]["it"], "en": NEW["names"]["en"]}, "scientific_name": "Tuber magnatum",
                 "added_from_sources": "deroga decisa dall'utente il 2026-11-05: nessuna scheda CREA/BDA; stagionalità da Legge 752/1985"})
    base["botany_check"]["scientific_name_draft"] = "Tuber magnatum"
    base["botany_check"]["eppo"].update({"eppo_code": "TUERMA", "matched_on": "Tuber magnatum", "eppo_preferred_name": "Tuber magnatum",
                                         "common_names": {"it": NEW["names"]["synonyms"]["it"], "en": NEW["names"]["synonyms"]["en"]},
                                         "url": "https://gd.eppo.int/taxon/TUERMA"})
    base["botany_check"]["gbif"] = {"status": "exact", "gbif_key": 5258456, "name": "Tuber magnatum Picco", "family": "Tuberaceae",
                                    "url": "https://www.gbif.org/species/5258456"}
    base["sources"]["crea"] = None
    base["sources"]["bda_ieo"] = None
    base["sources"]["eufic_keys"] = NEW["eufic_keys"]
    idx["items"].insert(next(i for i, x in enumerate(idx["items"]) if x["id"] == NEW["from"]) + 1, base)
    idx["total_items"] = len(idx["items"])
    save_json(DATA / "items_index.json", idx)


def main():
    db = load_json(DATA / "database.json")
    it = build(db)
    index_entry()
    save_json(DATA / "database.json", db)
    print("added" if it else "already present", NEW["id"], "| products:", len(db["items"]))


if __name__ == "__main__":
    main()

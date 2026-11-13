"""Step 1.3f - Botany (EPPO common names -> IT/EN synonyms) and clean-up of invalid agronomic parameters from the draft.

- names.synonyms: IT/EN common names from the EPPO API (cache data/raw/eppo_cache.json), excluding the main name.
- botany.family: if missing, from WFO (family in the 'placement') or GBIF for mushrooms; differences from the draft
  stay flagged in the notes (e.g. Chenopodiaceae in WFO vs Amaranthaceae APG IV).
- draft agronomic_params with 0 values (e.g. 0 cm spacing) -> null (meaningless value).
Usage:  python scripts/enrich_botany.py
"""
from common import DATA, RAW, finalize_completeness, load_json, mark_enriched, save_json


def main():
    db = load_json(DATA / "database.json")
    idx = {i["id"]: i for i in load_json(DATA / "items_index.json")["items"]}
    cache = load_json(RAW / "eppo_cache.json")
    n_syn = n_fix = 0
    for it in db["items"]:
        b = idx[it["id"]]["botany_check"]
        code = it["botany"]["eppo_code"]
        names = cache.get(f"names|{code}") if code else None
        if isinstance(names, list):
            main_it, main_en = it["names"]["it"].lower(), it["names"]["en"].lower()
            it_syn = sorted({n["fullname"] for n in names if n.get("lang_iso") == "it" and n["fullname"].lower() != main_it})[:6]
            en_syn = sorted({n["fullname"] for n in names if n.get("lang_iso") == "en" and n["fullname"].lower() != main_en})[:6]
            if it_syn or en_syn:
                it["names"]["synonyms"] = {"it": it_syn, "en": en_syn}
                mark_enriched(it, ["names.synonyms"])
                n_syn += 1
        if not it["botany"]["family"]:
            fam = (b.get("wfo") or {}).get("family") or (b.get("gbif") or {}).get("family")
            if fam:
                it["botany"]["family"] = fam
                mark_enriched(it, ["botany.family"])
        if not it["botany"]["genus"]:
            it["botany"]["genus"] = it["botany"]["scientific_name"].split()[0]
        ap = it["agricultural_calendar_italy"]["agronomic_params"]
        if ap:
            sp = ap.get("plant_spacing_cm")
            if sp and (not sp.get("between_rows") or not sp.get("between_plants")):
                ap["plant_spacing_cm"] = None; n_fix += 1
                it["data_completeness"]["notes"] += " Sesto d'impianto della bozza con valore 0: rimosso."
            if ap.get("sowing_depth_cm") == 0:
                ap["sowing_depth_cm"] = None; n_fix += 1
            if all(v is None for v in ap.values()):
                it["agricultural_calendar_italy"]["agronomic_params"] = None
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(f"sinonimi EPPO: {n_syn} alimenti; parametri agronomici non validi rimossi: {n_fix}")


if __name__ == "__main__":
    main()

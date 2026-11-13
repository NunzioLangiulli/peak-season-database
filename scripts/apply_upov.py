"""UPOV species code of the EU Common Catalogue (botany.upov_code / upov_name / upov_register).

The UPOV code identifies the species in the EU and national variety registers (EU Plant Variety Portal, CPVO, national
registers): it links the product to the official list of registered varieties. Unregulated species
(culinary herbs, mushrooms, tropical fruit, grapevine...) -> null, field not applicable.
Usage:  python scripts/apply_upov.py
"""
from common import DATA, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na

URL = "https://ec.europa.eu/food/plant-variety-portal/"


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "upov_species.json")["items"]
    cnt = load_json(ROOT / "scripts" / "config" / "eu_variety_counts_it.json")
    db = load_json(DATA / "database.json")
    n = 0
    for it in db["items"]:
        b = it["botany"]
        m = cfg.get(it["id"])
        if m:
            b["upov_code"], b["upov_name"], b["upov_register"] = m[0], m[1], m[2]
            b["upov_match"] = m[3]
            b["upov_note"] = m[4] if len(m) > 4 else None
            mark_enriched(it, ["botany.upov_code", "botany.upov_name", "botany.upov_register"])
            k = cnt["counts"].get(m[0])
            b["varieties_registered_italy"] = None if k is None else {
                "count": k, "upov_code": m[0], "status": "Registered", "checked": cnt["checked"], "source": URL}
            if b["varieties_registered_italy"] and not k:
                b["varieties_registered_italy"]["note"] = "nessuna varietà iscritta con questo codice: possono essere iscritte sotto un codice affine"
            mark_enriched(it, ["botany.varieties_registered_italy"])
            if URL not in it["sources_by_topic"]["other_urls"]:
                it["sources_by_topic"]["other_urls"].append(URL)
            n += 1
        else:
            b.update({"upov_code": None, "upov_name": None, "upov_register": None, "upov_match": None, "upov_note": None,
                      "varieties_registered_italy": None})
        set_na(it, [f"botany.{k}" for k in ("upov_code", "upov_name", "upov_register", "upov_match", "upov_note", "varieties_registered_italy") if b.get(k) is None])
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(f"codice UPOV assegnato a {n} alimenti su {len(db['items'])}")


if __name__ == "__main__":
    main()

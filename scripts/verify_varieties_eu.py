"""Second check of the draft's varieties: EU Common Catalogue (EU Plant Variety Portal).

The matches are in config/eu_variety_portal_matches.json (search done in the browser on 2026-11-04, UPOV species
checked by hand). Confirmed varieties go back into notable_varieties with their source; the others stay in
draft_legacy_values.json (notable_varieties_unverified).
Usage:  python scripts/verify_varieties_eu.py   (after verify_varieties.py)
"""
from common import DATA, ROOT, finalize_completeness, load_json, mark_enriched, save_json

URL = "https://ec.europa.eu/food/plant-variety-portal/"
K = "italian_varieties_and_territories.notable_varieties_unverified"
STATUS_IT = {"Registered": "iscritta", "Surrendered": "cancellata", "Expired": "scaduta"}


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "eu_variety_portal_matches.json")["matches"]
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    items = {it["id"]: it for it in db["items"]}
    n = 0
    for m in cfg:
        it = items[m["item"]]
        iv = it["italian_varieties_and_territories"]
        if iv.get("notable_varieties") is None:
            iv["notable_varieties"] = []
        lg = legacy["items"].get(m["item"], {})
        recs = [dict(zip(("country", "status", "uuid"), r.split(":", 2))) for r in m["records"]]
        src = {"source_key": "eu_plant_variety_portal", "url": URL, "list": "common_catalogue",
               "registered_name": m["registered"], "upov_code": m["upov"], "match": m["match"], "records": recs}
        if m["draft"] in iv["notable_varieties"]:
            # already verified by other sources: only adds the EU Catalogue listing
            for e in iv.get("varieties_verification", []):
                if e["name"] == m["draft"] and not any(s["source_key"] == "eu_plant_variety_portal" for s in e["sources"]):
                    e["sources"].append(src)
            continue
        now = [r["country"] for r in recs if r["status"] == "Registered"]
        past = [r["country"] for r in recs if r["status"] != "Registered"]
        note = (f"Catalogo comune UE: registrata come '{m['registered']}' (specie UPOV {m['upov']}); "
                + (f"iscritta in {', '.join(now)}" if now else "oggi non piu' iscritta")
                + (f"; cancellata/scaduta in {', '.join(past)}" if past else "")
                + (f". {m['note']}" if m.get("note") else "") + ".")
        iv["notable_varieties"].append(m["draft"])
        iv.setdefault("varieties_verification", []).append({
            "name": m["draft"], "verified": True, "note": note,
            "sources": [{"source_key": "eu_plant_variety_portal", "url": URL, "list": "common_catalogue",
                         "registered_name": m["registered"], "upov_code": m["upov"], "match": m["match"], "records": recs}]})
        if K in lg:
            lg[K] = [v for v in lg[K] if v != m["draft"]]
            if not lg[K]:
                del lg[K]
        mark_enriched(it, ["italian_varieties_and_territories.notable_varieties"])
        finalize_completeness(it)
        n += 1
    # removes the leftover "not verified" entries for varieties later confirmed by the EU Catalogue
    for it in db["items"]:
        iv = it["italian_varieties_and_territories"]
        ok = {e["name"] for e in iv.get("varieties_verification") or [] if e.get("verified")}
        iv["varieties_verification"] = [e for e in iv.get("varieties_verification") or [] if e.get("verified") or e["name"] not in ok]
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    left = sum(len(v.get(K, [])) for v in legacy["items"].values())
    print(f"varieta' confermate dal Catalogo UE: {n}; ancora non verificate: {left}")


if __name__ == "__main__":
    main()


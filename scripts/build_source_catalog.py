"""Catalogue of sources and conflicts at the top of the database (metadata.official_sources, metadata.source_conflicts).

For each source adds: description (what it is), authority (why it is authoritative), offers (what it offers), used_for (topics,
number and list of the products for which it was consulted, computed from the records). Adds the general cases of conflict
between sources with the decision taken (config/source_conflicts.json).
Usage:  python scripts/build_source_catalog.py   (after build_source_registry.py and build_help.py)
"""
import collections

from common import DATA, ROOT, load_json, save_json

TOPIC = {  # etichette bilingui degli argomenti
    "nutrition": ("Nutrizione", "Nutrition"), "edible_portion": ("Parte edibile", "Edible portion"), "bioactive_compounds": ("Composti bioattivi", "Bioactive compounds"),
    "nutrition_claims": ("Claim UE", "EU claims"), "percent_nrv": ("%VNR", "%NRV"), "allergens": ("Allergeni", "Allergens"), "reference_intakes": ("LARN", "LARN"),
    "reference_portion": ("Porzioni", "Portions"), "seasonality": ("Stagionalità", "Seasonality"), "seasonality_europe": ("Stagionalità europea", "European seasonality"),
    "agricultural_calendar": ("Calendario agricolo", "Growing calendar"), "agronomic_params": ("Parametri di coltivazione", "Growing parameters"),
    "postharvest": ("Post-raccolta", "Postharvest"), "ethylene": ("Etilene", "Ethylene"), "chilling_injury": ("Danno da freddo", "Chilling injury"),
    "storage_compatibility": ("Conservazione compatibile", "Compatible storage"), "home_storage": ("Conservazione in casa", "Home storage"),
    "botany": ("Botanica", "Botany"), "botany_upov_code": ("Codice UPOV", "UPOV code"), "varieties": ("Varietà", "Varieties"), "dop_igp": ("DOP/IGP", "PDO/PGI"),
    "traditional_products": ("Prodotti tradizionali", "Traditional products"), "environmental_footprint": ("Impronta ambientale", "Environmental footprint"),
    "images": ("Immagini", "Images"), "health_notes": ("Note di salute", "Health notes"), "texts": ("Testi", "Texts"),
}


def main():
    db = load_json(DATA / "database.json")
    desc = load_json(ROOT / "scripts" / "config" / "source_descriptions.json")["sources"]
    conf = load_json(ROOT / "scripts" / "config" / "source_conflicts.json")["conflicts"]
    use = collections.defaultdict(lambda: {"topics": set(), "items": set()})
    for it in db["items"]:
        for s in it["sources_by_topic"]["sources_used"]:
            u = use[s["source_key"]]
            u["topics"].update(s["topics"])
            u["items"].add(it["id"])
    glos = {}
    for gid, g in (db["metadata"].get("glossary") or {}).items():
        for s in g["sources"]:
            glos.setdefault(s["key"], []).append(gid)
    missing = []
    for s in db["metadata"]["official_sources"]:
        d = desc.get(s["key"])
        if not d:
            missing.append(s["key"])
            continue
        for k in ("what", "authority", "offers"):
            s[{"what": "description"}.get(k, k)] = {"it": d[k][0], "en": d[k][1]}
        u = use.get(s["key"], {"topics": set(), "items": set()})
        s["used_for"] = {
            "topics": [{"key": t, "label": {"it": TOPIC.get(t, (t, t))[0], "en": TOPIC.get(t, (t, t))[1]}} for t in sorted(u["topics"])],
            "items_count": len(u["items"]), "items": sorted(u["items"]),
            "glossary_entries": sorted(glos.get(s["key"], [])),
            "database_level": s["key"] in ("eufic_article", "eufic_national", "eea_biogeo"),
        }
    db["metadata"]["source_conflicts"] = [{
        "id": c["id"], "topic": c["topic"], "sources": c["sources"],
        **{k: {"it": c[k][0], "en": c[k][1]} for k in ("issue", "why", "decision", "rationale")}} for c in conf]
    save_json(DATA / "database.json", db)
    print(f"fonti descritte: {len(db['metadata']['official_sources']) - len(missing)}; senza descrizione: {missing}; conflitti: {len(conf)}")


if __name__ == "__main__":
    main()

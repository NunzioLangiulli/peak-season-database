"""Applica le classi di produzione di etilene corrette sui capitoli di USDA HB66 (config/ethylene_curated.json),
ricalcola keep_away_from per tutti gli alimenti sensibili (produttori di classe alta o superiore) e aggiunge la nota
della fonte a compatibility_notes. Idempotente.
Uso:  python scripts/apply_ethylene_curated.py   (dopo apply_hb66_curated.py; poi apply_texts.py, che rigenera
      le note, e di nuovo questo script per riaggiungere le note curate)
"""
from common import CONFIG, DATA, finalize_completeness, load_json, mark_enriched, save_json

STRONG = ("high", "very_high", "extremely_high")
PRODUCER = ("moderate",) + STRONG


def main():
    db = load_json(DATA / "database.json")
    cfg = load_json(CONFIG / "ethylene_curated.json")["items"]
    I = {i["id"]: i for i in db["items"]}
    E = lambda it: it["ripening_and_storage"]["ethylene_compatibility"]  # noqa: E731
    for iid, c in cfg.items():
        e = E(I[iid])
        e["ethylene_production_class"] = c["class"]
        e["produces_ethylene"] = c["class"] in PRODUCER
        dc = I[iid]["data_completeness"]
        q = f"Etilene: classe '{c['class']}' dal capitolo USDA HB66 p. {c['page']} (valore a 20 °C del frutto maturo): \"{c['quote']}\""
        if q not in dc["notes"]:
            dc["notes"] = (dc["notes"] + " " + q).strip()
        mark_enriched(I[iid], ["ripening_and_storage.ethylene_compatibility.ethylene_production_class"])
    strong = [i["id"] for i in db["items"] if E(i).get("ethylene_production_class") in STRONG]
    for it in db["items"]:
        e = E(it)
        e["keep_away_from"] = [p for p in strong if p != it["id"]] if e.get("sensitive_to_ethylene") is True else []
        c = cfg.get(it["id"])
        if c and e.get("compatibility_notes"):
            n = e["compatibility_notes"]
            if c["note"][0] not in n["it"]:
                n["it"] = n["it"].rstrip() + " " + c["note"][0]
                n["en"] = n["en"].rstrip() + " " + c["note"][1]
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print("produttori forti:", strong)


if __name__ == "__main__":
    main()

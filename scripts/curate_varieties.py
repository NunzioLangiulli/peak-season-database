"""Hand-curated fixes and additions to the varieties (2026-11-05). Idempotent.

1. Pesca Tabacchiera dell'Etna as a variety of peach (owner decision): Slow Food Ark of Taste,
   page in data/raw/slowfood_pages/pesca-tabacchiera-delletna.html ("forma schiacciata ... tanto schiacciata da
   sembrare una tabacchiera"; municipalities of Adrano, Biancavilla, Bronte, Maniace, Mojo Alcantara, Roccella Valdemone).
2. Wrong Slow Food links produced by the automatic word matching (verify_varieties.py): removed.
   The varieties stay verified if they have other sources.
Usage:  python scripts/curate_varieties.py   (after verify_varieties_eu.py / merge_items.py)
"""
from common import DATA, finalize_completeness, load_json, mark_enriched, save_json

SF = "https://www.fondazioneslowfood.com/it/arca-del-gusto-slow-food/"
ADD = {
    "pesca_peach": {
        "name": "Pesca Tabacchiera dell'Etna",
        "verified": True,
        "note": {"it": "Pesca piatta a pasta bianca, così schiacciata da sembrare una tabacchiera; prodotta sull'Etna e nella Valle dell'Alcantara (CT, ME). Arca del Gusto Slow Food.",
                 "en": "White-fleshed flat peach, so flattened that it resembles a snuffbox; grown on Mount Etna and in the Alcantara Valley (Catania, Messina). Slow Food Ark of Taste."},
        "sources": [{"source_key": "slow_food", "url": SF + "pesca-tabacchiera-delletna/", "list": "arca_del_gusto",
                     "local_file": "data/raw/slowfood_pages/pesca-tabacchiera-delletna.html"}],
    },
}
WRONG_SF = {  # (product, variety) -> Slow Food page matched by mistake
    ("bietola_da_coste_swiss_chard", "Bietola Verde a Costa Bianca Gigante"): "pisello-lagrima-de-costa-di-gipuzkoa",
    ("fico_fig", "Fico Bianco del Cilento DOP"): "fico-monnato-di-prignano-cilento",
    ("lattuga_da_cespo_head_lettuce", "Lattuga Romana"): "lattuga-romana-kesseler-strunkchen",
}


def main():
    db = load_json(DATA / "database.json")
    I = {i["id"]: i for i in db["items"]}
    for iid, v in ADD.items():
        iv = I[iid]["italian_varieties_and_territories"]
        vv = iv.setdefault("varieties_verification", []) or []
        if not any(x["name"] == v["name"] for x in vv):
            vv.append(v)
            iv["varieties_verification"] = vv
            iv["notable_varieties"] = (iv.get("notable_varieties") or []) + [v["name"]]
            mark_enriched(I[iid], ["italian_varieties_and_territories.notable_varieties"])
            print("added", iid, v["name"])
    for (iid, name), slug in WRONG_SF.items():
        it = I.get(iid)
        if not it:
            continue
        for v in it["italian_varieties_and_territories"].get("varieties_verification") or []:
            if v["name"] == name:
                before = len(v["sources"])
                v["sources"] = [s for s in v["sources"] if slug not in s.get("url", "")]
                if len(v["sources"]) < before:
                    print("removed wrong Slow Food link:", iid, name, "| remaining sources", [s["source_key"] for s in v["sources"]])
                if not v["sources"]:
                    v["verified"] = False
    for it in I.values():
        finalize_completeness(it)
    save_json(DATA / "database.json", db)


if __name__ == "__main__":
    main()

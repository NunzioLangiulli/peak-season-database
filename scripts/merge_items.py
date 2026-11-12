"""Unisce alimenti che l'utente ha deciso di non tenere separati (decisione del 2026-11-05).

- bietola_da_taglio_leaf_beet -> bietola_da_coste_swiss_chard ("Bietola"): stessa specie e stessa scheda CREA/BDA
  (005080 / 307); da coste e da taglio differiscono per forma di raccolta e uso in cucina, non per i dati.
  Si tiene l'id della bietola da coste (usato da configurazioni, testi e immagini); la scheda unita copre entrambe
  le forme (nomi alternativi, testi in scripts/texts/block_01.json, varietà, immagini).
La scheda tolta è archiviata in data/merged_items_archive.json; i riferimenti da altre schede sono riallineati.
Uso:  python scripts/merge_items.py   (dopo apply_texts.py; idempotente)
"""
import json

from common import DATA, IMAGES, finalize_completeness, load_json, mark_enriched, save_json

MERGES = {
    "bietola_da_taglio_leaf_beet": {
        "into": "bietola_da_coste_swiss_chard",
        "names": {"it": "Bietola", "en": "Chard",
                  "synonyms": {"it": ["bieta", "bietola da coste", "bietola da taglio", "erbetta", "bieta a foglia", "bietola bianca"],
                               "en": ["Swiss chard", "leaf beet", "perpetual spinach", "silver beet", "spinach beet", "chard beet", "foliage beet"]}},
        "scientific_name": "Beta vulgaris subsp. vulgaris",
        "note": "Scheda unita alla bietola da taglio (erbetta) il 2026-11-05 su decisione dell'utente: stessa specie (EPPO BEAVV, UPOV Leaf Beet Group) e stessa scheda CREA 005080 / BDA-IEO 307. Stagionalità e calendario agricolo sono quelli della bietola da coste (tutto l'anno), che comprendono quelli della bietola da taglio.",
    },
}


def replace_refs(o, old, new):
    if isinstance(o, dict):
        return {k: replace_refs(v, old, new) for k, v in o.items()}
    if isinstance(o, list):
        if old not in o:
            return [replace_refs(x, old, new) for x in o]
        out = []
        for v in (new if x == old else x for x in o):  # lista di id: sostituisce e toglie il doppione
            if v not in out:
                out.append(v)
        return out
    return new if o == old else o


def main():
    db = load_json(DATA / "database.json")
    arch_path = DATA / "merged_items_archive.json"
    arch = load_json(arch_path) if arch_path.exists() else {"_doc": "Schede unite ad altre (merge_items.py), conservate integre.", "items": {}}
    meta = load_json(IMAGES / "_metadata.json")
    for old, m in MERGES.items():
        src = next((i for i in db["items"] if i["id"] == old), None)
        if src is None:
            print(f"{old}: già unita")
            continue
        dst = next(i for i in db["items"] if i["id"] == m["into"])
        arch["items"][old] = {"merged_into": m["into"], "item": src}
        dst["names"] = m["names"]
        dst["botany"]["scientific_name"] = m["scientific_name"]
        # varietà: unione
        iv, sv = dst["italian_varieties_and_territories"], src["italian_varieties_and_territories"]
        names = {v["name"] for v in iv.get("varieties_verification") or []}
        iv["varieties_verification"] = (iv.get("varieties_verification") or []) + [v for v in sv.get("varieties_verification") or [] if v["name"] not in names]
        nv = list(iv.get("notable_varieties") or [])
        nv += [v for v in sv.get("notable_varieties") or [] if v not in nv]
        iv["notable_varieties"] = nv or None
        # immagini: rinomina e accoda
        n = len(dst["images"]["gallery"])
        for det in src["images"]["image_details"]:
            f = IMAGES / det["filename"]
            if not f.exists():
                continue
            n += 1
            new = f"{m['into']}_{n:02d}.jpg"
            while (IMAGES / new).exists():
                n += 1
                new = f"{m['into']}_{n:02d}.jpg"
            f.rename(IMAGES / new)
            if det["filename"] in meta:
                meta[new] = {**meta.pop(det["filename"]), "filename": new}
            dst["images"]["gallery"].append(new)
            dst["images"]["image_details"].append({**det, "filename": new})
        dc = dst["data_completeness"]
        if m["note"] not in dc["notes"]:
            dc["notes"] = (dc["notes"] + " " + m["note"]).strip()
        mark_enriched(dst, ["names", "italian_varieties_and_territories", "images"])
        db["items"] = [i for i in db["items"] if i["id"] != old]
        db["items"] = [replace_refs(i, old, m["into"]) for i in db["items"]]
        finalize_completeness(dst)
        print(f"{old} -> {m['into']}: immagini {len(dst['images']['gallery'])}, varietà {len(iv['varieties_verification'])}")
    save_json(IMAGES / "_metadata.json", meta)
    save_json(arch_path, arch)
    save_json(DATA / "database.json", db)
    print("alimenti:", len(db["items"]), "| riferimenti residui:", json.dumps(db, ensure_ascii=False).count(next(iter(MERGES))))


if __name__ == "__main__":
    main()

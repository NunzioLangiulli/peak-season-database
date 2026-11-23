"""Removes products that the owner decided not to keep (decision of 2026-11-23), like merge_items.py does for merges.

- cicoria_da_cespo_chicory ("Cicoria da Cespo (Catalogna / Pan di Zucchero)") is removed: its nutrition values were
  only an approximation (CREA 005240 "Cicoria, di campo"). The owner keeps cicoria_da_taglio_cutting_chicory, which
  has exact entries (CREA 005230, BDA-IEO 320), and renames it simply "Cicoria" / "Chicory". The id stays the same
  because favourites saved in the app use it.
The removed record is archived whole in data/merged_items_archive.json ("removed_on", "replaced_by", "reason").
References from other records (storage compatibility, sources used_for) point to the kept product, without duplicates;
the per-product inputs of the scripts (scripts/config/*.json, scripts/texts/block_*.json, data/items_index.json) drop
the removed id, so later runs do not bring it back. Photos are removed through the Admin Studio (Images tab).
Usage:  python scripts/remove_items.py   (idempotent)
"""
import json
from pathlib import Path

from common import CONFIG, DATA, finalize_completeness, load_json, mark_enriched, save_json
from merge_items import replace_refs

ROOT = Path(__file__).resolve().parent.parent
REMOVALS = {
    "cicoria_da_cespo_chicory": {
        "replaced_by": "cicoria_da_taglio_cutting_chicory",
        "reason": "Owner's decision of 2026-11-23: only the chicory with exact CREA/BDA-IEO entries is kept (cutting "
                  "chicory, CREA 005230 / BDA-IEO 320), named simply 'Cicoria'. This record used approximate values "
                  "(CREA 005240 'Cicoria, di campo').",
    },
}
RENAMES = {
    "cicoria_da_taglio_cutting_chicory": {
        "it": "Cicoria", "en": "Chicory",
        # other chicory types that have their own record (Belgian endive, radicchio) or that the sources do not give
        # for this product are dropped from the synonyms
        "synonyms": {"it": ["Cicoria da Taglio", "Cicorino", "Cicoria Amara"],
                     "en": ["Cutting Chicory", "Leaf Chicory", "Succory"]},
        "note": "Rinominata 'Cicoria' il 2026-11-23 su decisione dell'utente, dopo la rimozione della cicoria da cespo "
                "(scheda archiviata in data/merged_items_archive.json).",
    },
}


def drop_id(o, old):
    """Removes dict keys equal to the id, list items equal to the id and list entries whose id/item field is the id."""
    if isinstance(o, dict):
        return {k: drop_id(v, old) for k, v in o.items() if k != old}
    if isinstance(o, list):
        return [drop_id(x, old) for x in o
                if x != old and not (isinstance(x, dict) and old in (x.get("id"), x.get("item")))]
    return o


def clean_file(path, old):
    raw = path.read_bytes().decode("utf-8")
    if old not in raw:
        return False
    data = json.loads(raw)
    new = drop_id(data, old)
    indent = 1 if raw.startswith("{\r\n \"") or raw.startswith("{\n \"") else 2
    out = json.dumps(new, ensure_ascii=False, indent=indent) + "\n"
    if "\r\n" in raw:
        out = out.replace("\n", "\r\n")
    path.write_bytes(out.encode("utf-8"))
    return True


def main():
    db = load_json(DATA / "database.json")
    arch_path = DATA / "merged_items_archive.json"
    arch = load_json(arch_path)
    for old, r in REMOVALS.items():
        src = next((i for i in db["items"] if i["id"] == old), None)
        if src is None:
            print(f"{old}: already removed")
        else:
            arch["items"][old] = {"removed_on": "2026-11-23", "replaced_by": r["replaced_by"], "reason": r["reason"],
                                  "item": src}
            db["items"] = [i for i in db["items"] if i["id"] != old]
            db["items"] = [replace_refs(i, old, r["replaced_by"]) for i in db["items"]]
            db["metadata"] = replace_refs(db["metadata"], old, r["replaced_by"])
            print(f"{old}: archived and removed; references now point to {r['replaced_by']}")
        # image search inputs (image_*.json) are left to the Admin Studio, which removes the photos
        files = [p for p in sorted(CONFIG.glob("*.json")) if not p.name.startswith("image_")]
        changed = [str(p.relative_to(ROOT)) for p in files + sorted((CONFIG.parent / "texts").glob("block_*.json"))
                   if clean_file(p, old)]
        idx = DATA / "items_index.json"
        if old in idx.read_text(encoding="utf-8"):
            ix = load_json(idx)
            for k in ("from_draft", "new_items", "items"):
                if isinstance(ix.get(k), list):
                    ix[k] = [x for x in ix[k] if not (isinstance(x, dict) and x.get("id") == old) and x != old]
            if isinstance(ix.get("total_items"), int):
                ix["total_items"] = len(db["items"])
            save_json(idx, ix)
            changed.append("data/items_index.json")
        print("  inputs cleaned:", changed)
    for iid, n in RENAMES.items():
        it = next(i for i in db["items"] if i["id"] == iid)
        if it["names"].get("it") != n["it"]:
            it["names"] = {"it": n["it"], "en": n["en"], "synonyms": n["synonyms"]}
            dc = it["data_completeness"]
            if n["note"] not in (dc.get("notes") or ""):
                dc["notes"] = ((dc.get("notes") or "") + " " + n["note"]).strip()
            mark_enriched(it, ["names"])
            finalize_completeness(it)
            print(f"{iid}: renamed to {n['it']} / {n['en']}")
    save_json(arch_path, arch)
    save_json(DATA / "database.json", db)
    print("products:", len(db["items"]), "| remaining references:",
          sum(json.dumps(db, ensure_ascii=False).count(o) for o in REMOVALS))


if __name__ == "__main__":
    main()

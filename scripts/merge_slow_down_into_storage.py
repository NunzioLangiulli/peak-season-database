"""Merge the slow_down advice of non-climacteric produce into storage_instructions (user request, 2026-11-13). Idempotent.

For non-climacteric produce the app no longer shows ripening_management.slow_down ("Per Conservarlo più a Lungo"):
the user found it almost always redundant with storage_instructions. This script adds to storage_instructions only the
pieces of slow_down that the paragraph does not already say:
- where to keep it (fridge / cool, dry, dark place / cool place away from sun and heat), unless the paragraph already
  names a place (fridge, pantry, cool place);
- protection from drying out (fridge produce);
- the lowest safe temperature ("avoid temperatures below X °C"), only if the paragraph says nothing about cold, so
  that it never contradicts the paragraph's own figures.
"Away from ethylene-producing fruit" is not added when the item has a keep_away_from list: the app shows that list
right after the storage text. Sentences are written without gender or number ("Evita la disidratazione"), since the
paragraphs use both. slow_down itself stays in the database as data, but is no longer displayed.
Usage:  python scripts/merge_slow_down_into_storage.py [--dry-run]   (after apply_texts.py; then ux_terminology and
        title_case_labels)
"""
import re

from common import DATA, finalize_completeness, load_json, mark_enriched, save_json

PIECES = [  # (pattern in slow_down IT, "already said" pattern in storage_instructions IT, IT sentence, EN sentence)
    (r"in frigorifero", r"frigo", "Meglio in frigorifero.", "Best kept in the fridge."),
    (r"protetto dalla disidratazione", r"disidrat|sacchett|pellicol|contenitor|umid|avvolt|carta|panno|chius|acqua|brattee|liquido",
     "Evita la disidratazione.", "Avoid drying out."),
    (r"fresco, asciutto e buio", r"fresc|buio|asciutt|cantina|dispensa|frigo", "Meglio in un luogo fresco, asciutto e buio.",
     "Best in a cool, dry, dark place."),
    (r"lontano da sole e fonti di calore", r"fresc|sole|calore|ombra|frigo", "Meglio in un luogo fresco, lontano dal sole e da fonti di calore.",
     "Best in a cool place, away from sun and heat."),
]
ETHYLENE = (r"lontano da frutti che producono etilene", r"etilene",
            "Lontano dalla frutta che produce etilene.", "Away from ethylene-producing fruit.")


def additions(r):
    sd = ((r.get("ripening_management") or {}).get("slow_down") or {}).get("it") or ""
    si = ((r.get("storage_instructions") or {}).get("it") or "").lower()
    add = []
    for pat, said, it, en in PIECES:
        if re.search(pat, sd) and not re.search(said, si):
            add.append((it, en))
    e = r.get("ethylene_compatibility") or {}
    if re.search(ETHYLENE[0], sd) and not re.search(ETHYLENE[1], si) and not e.get("keep_away_from"):
        add.append(ETHYLENE[2:])
    m = re.search(r"inferiori a ([\d.]+) °C", sd)
    if m and not re.search(r"freddo|°c", si):          # the paragraph already discusses cold: keep its own figures
        t = m.group(1)
        add.append((f"Evita temperature inferiori a {t.replace('.', ',')} °C: soffre il freddo.",
                    f"Avoid temperatures below {t} °C: it is sensitive to cold."))
    return [a for a in add if a[0] not in ((r.get("storage_instructions") or {}).get("it") or "")]


def main(dry=False):
    db = load_json(DATA / "database.json")
    n_items, n_sent = 0, 0
    for it in db["items"]:
        r = it["ripening_and_storage"]
        if r.get("ripening_type") != "non_climaterico" or not r.get("storage_instructions"):
            continue
        add = additions(r)
        if not add:
            continue
        n_items += 1
        n_sent += len(add)
        if dry:
            print(it["id"], "+", " ".join(a[0] for a in add))
            continue
        si = r["storage_instructions"]
        si["it"] = si["it"].rstrip() + " " + " ".join(a[0] for a in add)
        si["en"] = si["en"].rstrip() + " " + " ".join(a[1] for a in add)
        mark_enriched(it, ["ripening_and_storage.storage_instructions"])
        finalize_completeness(it)
    if not dry:
        save_json(DATA / "database.json", db)
    print(f"products completed: {n_items}; sentences added: {n_sent}")


if __name__ == "__main__":
    import sys
    main("--dry-run" in sys.argv)

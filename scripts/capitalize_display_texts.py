"""Capital first letter in every text shown by the app (user rule, 2026-11-20). Rules and exceptions: display_case.py.

Also fixes the old spelling of the UPOV notes ("varieta'", "e'" -> "varietà", "è").
Run it last, after title_case_labels.py and build_nutrition_claims_rules.py; validate_db.py checks the result.
Usage:  python scripts/capitalize_display_texts.py
"""
import re

from common import DATA, load_json, save_json
import display_case

SPELLING = [("varieta'", "varietà"), (" e' ", " è "), ("piu'", "più")]
# proper nouns written in lower case in product texts (user rule: varieties, places, people... always capitalised;
# Italian adjectives such as "toscana" and official register names stay as they are). Also in scripts/texts/block_*.json.
PROPER = [(re.compile(r"\(catalogna, pan di zucchero\)"), "(Catalogna, Pan di Zucchero)"),
          (re.compile(r"\(catalogna, sugarloaf\)"), "(Catalogna, Sugarloaf)"),
          (re.compile(r"\bcatalogna\b"), "Catalogna")]


def fix_proper(o):
    n = 0
    if isinstance(o, dict):
        if isinstance(o.get("it"), str) and isinstance(o.get("en"), str):
            for lang in ("it", "en"):
                new = o[lang]
                for rx, rep in PROPER:
                    new = rx.sub(rep, new)
                if new != o[lang]:
                    o[lang] = new
                    n += 1
        for k, v in o.items():
            if k not in ("data_completeness", "sources_by_topic", "data_basis"):
                n += fix_proper(v)
    elif isinstance(o, list):
        for v in o:
            n += fix_proper(v)
    return n


def main():
    db = load_json(DATA / "database.json")
    n_spell = 0
    for it in db["items"]:
        note = (it.get("botany") or {}).get("upov_note")
        if isinstance(note, dict) and isinstance(note.get("it"), str):
            new = note["it"]
            for a, b in SPELLING:
                new = new.replace(a, b)
            if new != note["it"]:
                note["it"] = new
                n_spell += 1
    n_proper = sum(fix_proper(it) for it in db["items"])
    fixed = display_case.scan(db, fix=True)
    save_json(DATA / "database.json", db)
    print(f"texts capitalised: {len(fixed)}; proper nouns fixed: {n_proper}; UPOV notes respelled: {n_spell}")


if __name__ == "__main__":
    main()

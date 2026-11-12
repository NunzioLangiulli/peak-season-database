"""Pulisce data_completeness.notes: rimuove le frasi ripetute (gli script rieseguiti le accodano più volte) e tiene
solo l'ultima riga "Testi IT/EN riscritti ...". Da eseguire come ultimo passo della pipeline.
Uso:  python scripts/tidy_notes.py
"""
import re

from common import DATA, load_json, save_json


def main():
    db = load_json(DATA / "database.json")
    removed = 0
    for it in db["items"]:
        dc = it["data_completeness"]
        segs = [s.strip() for s in re.split(r"(?<=\.)\s+(?=[A-ZÀ-Ý])", dc["notes"] or "") if s.strip()]
        last_txt = max((i for i, s in enumerate(segs) if s.startswith("Testi IT/EN riscritti")), default=None)
        out, seen = [], set()
        for i, s in enumerate(segs):
            if s.startswith("Testi IT/EN riscritti") and i != last_txt:
                continue
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        removed += len(segs) - len(out)
        dc["notes"] = " ".join(out)
    save_json(DATA / "database.json", db)
    print("frasi duplicate rimosse:", removed)


if __name__ == "__main__":
    main()

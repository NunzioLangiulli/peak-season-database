"""Garden notes without chart repeats (user request, 2026-11-13). Idempotent.

The app draws separate rows from seedbed_sowing_months, direct_sowing_months, transplant_months and harvest_months,
so notes that only list those months add nothing:
- agricultural_calendar_italy.<area>.cultivation_notes that only repeat the chart ("Semina in semenzaio mar-apr, ...,
  raccolta giu-ott (Orto da Coltivare).") become null;
- the general note "Calendario ricavato dalla scheda di coltivazione di Orto da Coltivare." is dropped (the source is
  already in the links); its "Resa: ..." part, which explains how the chart was read, stays as "Nel calendario: ...";
- "(Orto da Coltivare)" is removed from any remaining note.
Notes with real extra information (tree habit, soil, pruning, harvest tips...) are kept. No note describes another
process with its own months (blanching, forcing...), so no extra_phases rows are needed today.
build_cultivation_notes.py and apply_curated_calendar.py write notes in this same form.
Usage:  python scripts/clean_garden_notes.py   (after build_cultivation_notes.py and apply_curated_calendar.py)
"""
import re

from common import DATA, finalize_completeness, load_json, save_json
from enrich_chilling import set_na

CHART_IT = re.compile(r"^((Semina in semenzaio|Semina diretta|Trapianto o messa a dimora|Trapianto|Raccolta|Messa a dimora)[^.;]*?,?\s*)+"
                      r"\(Orto da Coltivare\)\.$")
SRC_IT, SRC_EN = "Calendario ricavato dalla scheda di coltivazione di Orto da Coltivare.", "Calendar taken from the Orto da Coltivare growing guide."


def clean_general(n):
    """General note: source sentence dropped, 'Resa:' (how the chart was read) kept as 'Nel calendario:'."""
    it, en = n["it"].replace(SRC_IT, "").strip(), n["en"].replace(SRC_EN, "").strip()
    it, en = re.sub(r"^Resa:\s*", "Nel calendario: ", it), re.sub(r"^Rendering:\s*", "In the chart: ", en)
    return {"it": it, "en": en} if it and en else None


def strip_src(n):
    return {k: re.sub(r"\s*\(Orto da Coltivare\)", "", v) for k, v in n.items()}


def main():
    db = load_json(DATA / "database.json")
    st = {"area_notes_removed": 0, "general_notes_cleaned": 0, "general_notes_removed": 0}
    for it in db["items"]:
        cal = it["agricultural_calendar_italy"]
        na = []
        for a in ("nord", "centro", "sud_isole"):
            z = cal.get(a)
            n = (z or {}).get("cultivation_notes")
            if not n:
                continue
            if CHART_IT.match(n["it"]):
                z["cultivation_notes"] = None
                na.append(f"agricultural_calendar_italy.{a}.cultivation_notes")
                st["area_notes_removed"] += 1
            elif "(Orto da Coltivare)" in n["it"]:
                z["cultivation_notes"] = strip_src(n)
        g = cal.get("cultivation_notes")
        if g and SRC_IT in g["it"]:
            new = clean_general(g)
            cal["cultivation_notes"] = new
            st["general_notes_cleaned" if new else "general_notes_removed"] += 1
            if not new:
                na.append("agricultural_calendar_italy.cultivation_notes")
        if na:
            set_na(it, na)                       # empty on purpose: the chart rows already say it
            finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(st)


if __name__ == "__main__":
    main()

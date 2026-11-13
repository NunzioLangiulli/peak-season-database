"""Applies the hand-curated garden calendar (config/agricultural_calendar_curated.json) to the products added on
2026-11-05. Writes only the fields reported by the Orto da Coltivare sheet; the others stay empty. Idempotent.
Usage:  python scripts/apply_curated_calendar.py
"""
from common import CONFIG, DATA, finalize_completeness, load_json, mark_enriched, save_json

AB = {"it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
      "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
LAB = {"seed": ("semina in semenzaio", "seedbed sowing"), "direct": ("semina diretta", "direct sowing"),
       "transplant": ("trapianto o messa a dimora", "transplanting or planting"), "harvest": ("raccolta", "harvest")}


def ranges(ms, lang):
    """[11,12,1,2] -> 'nov-feb'; [3,4,9,10] -> 'mar-apr, set-ott'."""
    if not ms:
        return ""
    s = sorted(ms)
    runs, cur = [], [s[0]]
    for m in s[1:]:
        if m == cur[-1] + 1:
            cur.append(m)
        else:
            runs.append(cur)
            cur = [m]
    runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 12:   # a cavallo d'anno
        runs = [runs[-1] + runs[0]] + runs[1:-1]
    a = AB[lang]
    return ", ".join(a[r[0] - 1] if len(r) == 1 else f"{a[r[0] - 1]}-{a[r[-1] - 1]}" for r in runs)


def main():
    db = load_json(DATA / "database.json")
    cfg = load_json(CONFIG / "agricultural_calendar_curated.json")["items"]
    n = 0
    for it in db["items"]:
        c = cfg.get(it["id"])
        if not c:
            continue
        cal = it["agricultural_calendar_italy"]
        for area in ("nord", "centro", "sud_isole"):
            v = {k: c[k] for k in ("seed", "direct", "transplant", "harvest") if k in c}
            v.update((c.get("by_area") or {}).get(area, {}))
            a = cal[area]
            if "seed" in v:
                a["seedbed_sowing_months"] = v["seed"]
            if "direct" in v:
                a["direct_sowing_months"] = v["direct"]
            if "transplant" in v:
                a["transplant_months"] = v["transplant"]
            if "harvest" in v:
                a["harvest_months"] = v["harvest"]
            sow = sorted(set(v.get("seed", []) + v.get("direct", []) + v.get("transplant", [])))
            if sow:
                a["sowing_or_transplant_months"] = sow
            parts = {lang: ", ".join(f"{LAB[k][i]} {ranges(v[k], lang)}" for k in ("seed", "direct", "transplant", "harvest") if v.get(k))
                     for i, lang in enumerate(("it", "en"))}
            a["cultivation_notes"] = {"it": parts["it"][0].upper() + parts["it"][1:] + " (Orto da Coltivare).",
                                      "en": parts["en"][0].upper() + parts["en"][1:] + " (Orto da Coltivare)."}
        rule = c.get("rule")
        cal["cultivation_notes"] = {"it": "Calendario ricavato dalla scheda di coltivazione di Orto da Coltivare." + (f" Resa: {rule[0]}." if rule else ""),
                                    "en": "Calendar taken from the Orto da Coltivare growing guide." + (f" Rendering: {rule[1]}." if rule else "")}
        dc = it["data_completeness"]                     # verbatim quote: only in the internal notes (Italian)
        q = f"Calendario dell'orto, citazione da Orto da Coltivare: \"{c['quote']}\""
        if q not in dc["notes"]:
            dc["notes"] = (dc["notes"] + " " + q).strip()
        mark_enriched(it, [f"agricultural_calendar_italy.{a}" for a in ("nord", "centro", "sud_isole")])
        finalize_completeness(it)
        n += 1
    save_json(DATA / "database.json", db)
    print("calendari dell'orto applicati:", n)


if __name__ == "__main__":
    main()

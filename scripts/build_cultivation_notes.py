"""IT/EN growing notes generated from the verified Orto da Coltivare data (PDF tables for North/Centre/South).

- <zone>.cultivation_notes: no longer written (2026-11-13): the app draws the sowing, transplanting and harvest rows itself.
- cultivation_notes (general): sowing depth, spacing, exposure and moon phase given by ODC.
The draft's notes (unverified free text) go to draft_legacy_values.json.
Only for products with a row in the ODC tables; the others stay to be verified.
Usage:  python scripts/build_cultivation_notes.py
"""
from common import DATA, finalize_completeness, load_json, mark_enriched, save_json

A = "agricultural_calendar_italy"
MIT = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
MEN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SUN = {"molto_soleggiato": ("pieno sole", "full sun"), "soleggiato": ("posizione soleggiata", "sunny position"),
       "mezzombra": ("tollera la mezz'ombra", "tolerates partial shade"), "anche_mezzombra": ("anche a mezz'ombra", "also partial shade")}
MOON = {"fase_crescente": ("luna crescente", "waxing moon"), "fase_calante": ("luna calante", "waning moon")}


def cap(s):
    return s[:1].upper() + s[1:]


def runs(months):
    """Months -> consecutive ranges (also across the year end), e.g. [1,2,3,10,11,12] -> [(10,3)]."""
    s = sorted(set(months))
    if not s:
        return []
    if len(s) == 12:
        return [(1, 12)]
    out, start, prev = [], s[0], s[0]
    for m in s[1:]:
        if m == prev + 1:
            prev = m
            continue
        out.append((start, prev))
        start = prev = m
    out.append((start, prev))
    if len(out) > 1 and out[0][0] == 1 and out[-1][1] == 12:
        out = [(out[-1][0], out[0][1])] + out[1:-1]
    return out


def fmt(months, names):
    parts = []
    for a, b in runs(months):
        parts.append(names[a - 1] if a == b else f"{names[a - 1]}-{names[b - 1]}")
    return ", ".join(parts)


def zone_note(z):
    it, en = [], []
    for key, lit, len_ in (("seedbed_sowing_months", "semina in semenzaio", "seedbed sowing"),
                           ("direct_sowing_months", "semina diretta", "direct sowing"),
                           ("transplant_months", "trapianto", "transplanting"),
                           ("harvest_months", "raccolta", "harvest")):
        if z.get(key):
            it.append(f"{lit} {fmt(z[key], MIT)}")
            en.append(f"{len_} {fmt(z[key], MEN)}")
    if not it:
        return None
    return {"it": cap(", ".join(it)) + " (Orto da Coltivare).",
            "en": cap(", ".join(en)) + " (Orto da Coltivare)."}


def general_note(p):
    it, en = [], []
    if p.get("sowing_depth_cm"):
        it.append(f"profondità di semina {p['sowing_depth_cm']} cm".replace(".", ","))
        en.append(f"sowing depth {p['sowing_depth_cm']} cm")
    sp = p.get("plant_spacing_cm") or {}
    if sp.get("between_rows") and sp.get("between_plants"):
        it.append(f"distanze {sp['between_rows']} cm tra le file e {sp['between_plants']} cm sulla fila")
        en.append(f"spacing {sp['between_rows']} cm between rows and {sp['between_plants']} cm within the row")
    if p.get("sun_exposure") in SUN:
        it.append(SUN[p["sun_exposure"]][0])
        en.append(SUN[p["sun_exposure"]][1])
    if p.get("lunar_phase_advice") in MOON:
        it.append(f"ODC indica la semina con {MOON[p['lunar_phase_advice']][0]} (pratica tradizionale)")
        en.append(f"ODC suggests sowing with a {MOON[p['lunar_phase_advice']][1]} (traditional practice)")
    if not it:
        return None
    return {"it": cap("; ".join(it)) + ".", "en": cap("; ".join(en)) + "."}


def main():
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    n = 0
    for item in db["items"]:
        if not item["sources_by_topic"].get("source_codes", {}).get("odc_pdf_row"):
            continue
        cal = item[A]
        enr = []
        for zn in ("nord", "centro", "sud_isole"):
            z = cal[zn]
            note = None   # 2026-11-13: the app draws the chart rows (zone_note kept for reference); see clean_garden_notes.py
            if note:
                old = z.get("cultivation_notes")
                if old and old != note and "Orto da Coltivare" not in (old.get("it") or ""):
                    legacy["items"].setdefault(item["id"], {})[f"{A}.{zn}.cultivation_notes"] = old
                z["cultivation_notes"] = note
                enr.append(f"{A}.{zn}.cultivation_notes")
        g = general_note(cal.get("agronomic_params") or {})
        if g:
            cal["cultivation_notes"] = g
            enr.append(f"{A}.cultivation_notes")
        mark_enriched(item, enr)
        finalize_completeness(item)
        n += 1
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print("products with ODC growing notes:", n)
    ex = next(i for i in db["items"] if i["id"] == "aglio_garlic")[A]
    print(ex["nord"]["cultivation_notes"], ex["cultivation_notes"], sep="\n")


if __name__ == "__main__":
    main()

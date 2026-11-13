"""Audit of the seasonal curve (Phase 2 of the 2026-11-12 revision): peak_season coverage, "flat" curves,
isolated out-of-season gaps and discrepancies between harvest months (Orto da Coltivare) and Italian seasonality.
Writes data/seasonality_audit.json; does not modify the database.
Usage:  python scripts/audit_seasonality_curves.py
"""
import collections

from common import DATA, load_json, save_json

POS = {"primizie", "in_season", "peak_season", "end_of_season"}
AREAS = ("nord", "centro", "sud_isole")
ZONES = ("mediterranean", "continental", "atlantic", "boreal", "mountain", "pannonian")


def gaps(m):
    """Isolated out-of-season months (1-2 months) between two positive months, also across the year end."""
    if not m or not any(x in POS for x in m):
        return []
    out = []
    for i in range(12):
        if m[i] == "out_of_season":
            run = [i]
            j = (i + 1) % 12
            while m[j] == "out_of_season" and len(run) < 3:
                run.append(j)
                j = (j + 1) % 12
            if len(run) <= 2 and m[j] in POS and m[(i - 1) % 12] in POS:
                out.append([x + 1 for x in run])
    return [g for n, g in enumerate(out) if g not in out[:n]]


def main():
    db = load_json(DATA / "database.json")
    rep = {"items": {}, "summary": {}}
    peak_it = peak_zone = flat_it = flat_any = 0
    by_case = collections.Counter()
    for it in db["items"]:
        s, cal = it["seasonality"], it["agricultural_calendar_italy"]
        ita = s.get("italy_macro_areas") or {}
        zones = s.get("eufic_climatic_zones") or {}
        has_peak_it = any("peak_season" in (ita.get(a) or []) for a in AREAS)
        has_peak_zone = any("peak_season" in (zones.get(z) or []) for z in ZONES)
        states_it = {x for a in AREAS for x in (ita.get(a) or [])}
        flat = bool(states_it) and states_it <= {"in_season", "out_of_season"}
        peak_it += has_peak_it
        peak_zone += has_peak_zone
        flat_it += flat
        flat_any += flat and not has_peak_zone
        r = {"peak_italy": has_peak_it, "peak_eufic": has_peak_zone, "flat_italy": flat, "gaps": {}, "harvest_mismatch": {}}
        for a in AREAS:
            m = ita.get(a)
            g = gaps(m)
            if g:
                r["gaps"][a] = g
            hv = set((cal.get(a) or {}).get("harvest_months") or [])
            if m and hv:
                pos = {i + 1 for i, x in enumerate(m) if x in POS}
                only_h, only_s = sorted(hv - pos), sorted(pos - hv)
                if only_h or only_s:
                    r["harvest_mismatch"][a] = {"harvest_not_in_season": only_h, "season_not_harvest": only_s}
        rep["items"][it["id"]] = r
    rep["summary"] = {"items": len(db["items"]), "with_peak_italy": peak_it, "with_peak_eufic": peak_zone,
                      "flat_italy": flat_it, "flat_everywhere": flat_any,
                      "with_gaps": sum(1 for r in rep["items"].values() if r["gaps"]),
                      "with_harvest_mismatch": sum(1 for r in rep["items"].values() if r["harvest_mismatch"])}
    save_json(DATA / "seasonality_audit.json", rep)
    print(rep["summary"])


if __name__ == "__main__":
    main()

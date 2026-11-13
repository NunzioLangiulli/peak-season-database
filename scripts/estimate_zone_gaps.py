"""Seasonality estimates for zones without data (owner decision, 2026-11-06). Idempotent.

Estimates do NOT replace data: they go to seasonality.estimates, so the app can show them marked with "≈"
("Estimate from neighbouring zone") and the user can turn them off in Settings.

Rule (a single source per estimate, never an estimate from another estimate):
- European climate zones: the most similar neighbouring zone with real data is copied (EUFIC or national calendar
  cited by EUFIC), in the order of NEIGHBOURS (e.g. Pannonian <- Continental, then Alpine); failing that, for the
  Continental, Alpine and Pannonian zones, Northern Italy (continental climate); Atlantic and Boreal are not estimated
  from Italy (climate too different);
  for the Mediterranean zone, first the Italian South and Islands seasonality (Italy = Mediterranean country);
- Italian macro-areas: North <- Continental zone (then Alpine, Pannonian); Centre <- Mediterranean (then Continental);
  South and Islands <- Mediterranean;
- exotic fruit (same list as enrich_seasonality.EXOTIC_IF_NO_LOCAL + coconut): in zones without data nothing is
  estimated, the zone is marked "not_grown" ("Not grown here");
- with no neighbouring zone with data, the month stays "unknown" (no estimate).
Usage:  python scripts/estimate_zone_gaps.py   (after enrich_zone_gaps.py and before build_help.py)
"""
from common import DATA, load_json, save_json
from enrich_seasonality import EXOTIC_IF_NO_LOCAL

ZONES = ["mediterranean", "continental", "atlantic", "boreal", "mountain", "pannonian"]
NEIGHBOURS = {
    "pannonian": ["continental", "mountain", "italy:nord"],
    "mountain": ["continental", "pannonian", "italy:nord"],
    "continental": ["pannonian", "mountain", "atlantic", "italy:nord"],
    "atlantic": ["continental", "boreal"],
    "boreal": ["atlantic", "continental"],
    "mediterranean": ["italy:sud_isole", "continental"],
}
ITALY = {"nord": ["continental", "mountain", "pannonian"], "centro": ["mediterranean", "continental"], "sud_isole": ["mediterranean"]}
REAL = {"eufic_map", "austria_gesundheitsportal"}          # zones with real (not derived) data
EXOTIC = set(EXOTIC_IF_NO_LOCAL) | {"cocco_coconut"}


def months_ok(v):
    return isinstance(v, list) and len(v) == 12 and any(x != "not_applicable" for x in v)


def main():
    db = load_json(DATA / "database.json")
    stats = {"zone": 0, "italy": 0, "not_grown": 0, "unknown_zone": 0, "unknown_italy": 0}
    for it in db["items"]:
        s = it["seasonality"]
        z, src = s["eufic_climatic_zones"], s.get("eufic_zone_sources") or {}
        ita = s.get("italy_macro_areas") or {}
        real = {k: z[k] for k in ZONES if months_ok(z.get(k)) and (src.get(k) or {}).get("source") in REAL}
        italy_real = {a: v for a, v in ita.items() if months_ok(v) and not (s.get("italy_source") or {}).get("source", "").startswith("derived_")}
        est = {"eufic_climatic_zones": {}, "italy_macro_areas": {}, "not_grown": []}
        for k in ZONES:
            if z.get(k) is not None:
                continue
            if it["id"] in EXOTIC:
                est["not_grown"].append(k)
                stats["not_grown"] += 1
                continue
            for nb in NEIGHBOURS[k]:
                v = italy_real.get(nb.split(":")[1]) if nb.startswith("italy:") else real.get(nb)
                if v:
                    est["eufic_climatic_zones"][k] = {"months": list(v), "from": nb.replace("italy:", "italy_")}
                    stats["zone"] += 1
                    break
            else:
                stats["unknown_zone"] += 1
        for a, order in ITALY.items():
            if ita.get(a) is not None:
                continue
            for nb in order:
                if real.get(nb):
                    est["italy_macro_areas"][a] = {"months": list(real[nb]), "from": nb}
                    stats["italy"] += 1
                    break
            else:
                stats["unknown_italy"] += 1
        est = {k: v for k, v in est.items() if v}
        if est:
            s["estimates"] = est
        else:
            s.pop("estimates", None)
    db["metadata"]["seasonality_estimates_method"] = {
        "it": "Stime per le zone senza dato (seasonality.estimates), mostrate nell'app con \"≈\" come \"Stima dalla zona vicina\" e disattivabili dalle Impostazioni. "
              "Si copia la zona vicina più simile con dati veri: pannonica <- continentale, poi alpina, poi Nord Italia; alpina <- continentale, poi pannonica, poi Nord Italia; "
              "continentale <- pannonica, alpina, atlantica, poi Nord Italia; atlantica <- continentale, boreale; boreale <- atlantica, continentale; "
              "mediterranea <- Sud e Isole italiano, poi continentale. Macro-aree italiane: Nord <- continentale (poi alpina, pannonica), "
              "Centro <- mediterranea (poi continentale), Sud e Isole <- mediterranea. Mai una stima da un'altra stima. "
              "Frutti esotici: nelle zone senza dato \"Non coltivato qui\" (not_grown). Senza zone vicine con dati il mese resta non noto.",
        "en": "Estimates for zones with no data (seasonality.estimates), shown in the app with \"≈\" as \"Estimate from neighbouring zone\" and switchable off in Settings. "
              "The most similar neighbouring zone with real data is copied: Pannonian <- Continental, then Alpine, then Northern Italy; Alpine <- Continental, then Pannonian, then Northern Italy; "
              "Continental <- Pannonian, Alpine, Atlantic, then Northern Italy; Atlantic <- Continental, Boreal; Boreal <- Atlantic, Continental; "
              "Mediterranean <- Southern Italy and Islands, then Continental. Italian macro-areas: North <- Continental (then Alpine, Pannonian), "
              "Centre <- Mediterranean (then Continental), South and Islands <- Mediterranean. Never an estimate from another estimate. "
              "Exotic fruits: zones with no data are \"Not grown here\" (not_grown). With no neighbouring zone with data the month stays unknown."}
    save_json(DATA / "database.json", db)
    print(stats)


if __name__ == "__main__":
    main()

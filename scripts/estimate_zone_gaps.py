"""Stime di stagionalità per le zone senza dato (decisione dell'utente, 2026-11-06). Idempotente.

Le stime NON sostituiscono i dati: vanno in seasonality.estimates, così l'app può mostrarle marcate con "≈"
("Stima dalla zona vicina") e l'utente può disattivarle dalle Impostazioni.

Regola (una sola fonte per stima, mai una stima da un'altra stima):
- zone climatiche europee: si copia la zona vicina più simile che ha dati veri (EUFIC o calendario nazionale
  indicato da EUFIC), nell'ordine di NEIGHBOURS (es. pannonica <- continentale, poi alpina); in mancanza, per le
  zone continentale, alpina e pannonica, il Nord Italia (clima continentale); atlantica e boreale non si stimano
  dall'Italia (clima troppo diverso);
  per la zona mediterranea, prima la stagionalità di Sud e Isole italiana (Italia = Paese mediterraneo);
- macro-aree italiane: Nord <- zona continentale (poi alpina, pannonica); Centro <- mediterranea (poi continentale);
  Sud e Isole <- mediterranea;
- frutti esotici (stesso elenco di enrich_seasonality.EXOTIC_IF_NO_LOCAL + cocco): nelle zone senza dato non si
  stima nulla, la zona è segnata "not_grown" ("Non coltivato qui");
- senza nessuna zona vicina con dati il mese resta "non noto" (nessuna stima).
Uso:  python scripts/estimate_zone_gaps.py   (dopo enrich_zone_gaps.py e prima di build_help.py)
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
REAL = {"eufic_map", "austria_gesundheitsportal"}          # zone con dato vero (non derivato)
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

"""Italian seasonality for products that the seasonal calendars do not list (2026-11-05). Idempotent.

- Nectarine: the Italian calendars (WWF, Greenpeace, Altroconsumo, Orto da Coltivare) only list "peach", without
  separating the nectarine, which is the same species with smooth skin. The database's peach seasonality is used,
  declaring the derivation. Confirmations: the "Pesca e Nettarina di Romagna" PGI (eAmbrosia) protects peaches and
  nectarines together; EUFIC, where it lists nectarine (France, Spain), gives it the same months as peach.
- Truffles: harvest periods of Law no. 752 of 16 December 1985, art. 6 (data/raw/national_calendars/
  legge_752_1985_art6.html): Tuber magnatum 1 October-31 December; Tuber melanosporum 15 November-15 March.
  Regions may change the calendar by ordinance: this is the national calendar. Months only half covered
  are rendered as early (primizie) or end of season (end_of_season). Harvesting and selling fresh truffles is forbidden
  outside the period (art. 6), so the other months are out of season.
- Caesar's mushroom: Province of Cuneo, mushroom sheets (data/raw/national_calendars/provincia_cuneo_amanita_caesarea.html):
  "presente in estate ed inizio autunno". Declared rendering: June early, July-September in season, October end.
  The only institutional source found (Piedmont), applied to all macro-areas and declared as such.
No peak (peak only where at least two sources agree).
Usage:  python scripts/enrich_special_seasonality.py   (after enrich_seasonality.py)
"""
from common import DATA, finalize_completeness, load_json, mark_enriched, save_json

O, P, S, E = "out_of_season", "primizie", "in_season", "end_of_season"
L752 = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1985-12-16;752~art6"
CUNEO = "https://natura.provincia.cuneo.it/funghi/commestibili/amanita-caesarea/"
RULES = {
    "tartufo_nero_black_truffle": {
        "months": [S, S, E, O, O, O, O, O, O, O, P, S], "source": "legge_752_1985", "url": L752,
        "note": ("Calendario nazionale di raccolta della Legge 752/1985, art. 6: Tuber melanosporum dal 15 novembre al 15 marzo (novembre e marzo coperti a metà: inizio e fine stagione). Le regioni possono variarlo con ordinanza; fuori periodo raccolta e commercio del fresco sono vietati.",
                 "National harvest calendar of Italian Law 752/1985, art. 6: Tuber melanosporum from 15 November to 15 March (November and March half-covered: early and end of season). Regions may vary it by ordinance; outside this period harvesting and selling fresh truffles is forbidden.")},
    "tartufo_bianco_white_truffle": {
        "months": [O, O, O, O, O, O, O, O, O, S, S, S], "source": "legge_752_1985", "url": L752,
        "note": ("Calendario nazionale di raccolta della Legge 752/1985, art. 6: Tuber magnatum dal 1° ottobre al 31 dicembre. Le regioni possono variarlo con ordinanza; fuori periodo raccolta e commercio del fresco sono vietati.",
                 "National harvest calendar of Italian Law 752/1985, art. 6: Tuber magnatum from 1 October to 31 December. Regions may vary it by ordinance; outside this period harvesting and selling fresh truffles is forbidden.")},
    "fungo_ovolo_caesars_mushroom": {
        "months": [O, O, O, O, O, P, S, S, S, E, O, O], "source": "provincia_cuneo_funghi", "url": CUNEO,
        "note": ("Provincia di Cuneo, schede dei funghi commestibili: \"presente in estate ed inizio autunno\" (resa: giugno inizio, luglio-settembre di stagione, ottobre fine). Unica fonte istituzionale trovata, piemontese, applicata a tutta Italia. Vietato raccogliere l'ovolo chiuso (allo stadio di uovo).",
                 "Province of Cuneo, edible mushroom sheets: \"found in summer and early autumn\" (rendered as: June early, July-September in season, October end). The only institutional source found, from Piedmont, applied to all of Italy. Picking the closed 'egg' stage is forbidden.")},
}


def main():
    db = load_json(DATA / "database.json")
    I = {i["id"]: i for i in db["items"]}
    peach = I["pesca_peach"]["seasonality"]
    rules = dict(RULES)
    rules["pesca_noce_nectarine"] = {
        "areas": peach["italy_macro_areas"], "national": peach["italy_national"], "source": "derived_pesca", "url": None,
        "note": ("I calendari italiani (WWF, Greenpeace, Altroconsumo, Orto da Coltivare) non distinguono la pesca noce dalla pesca: è la stessa specie con buccia liscia e la stessa epoca di raccolta. Stagionalità ripresa dalla pesca del database. Lo conferma l'IGP \"Pesca e Nettarina di Romagna\", che le tutela insieme, ed EUFIC, che per Francia e Spagna dà alla nettarina gli stessi mesi della pesca.",
                 "Italian calendars (WWF, Greenpeace, Altroconsumo, Orto da Coltivare) do not distinguish nectarines from peaches: same species with smooth skin and the same harvest period. Seasonality taken from the database's peach. This is supported by the \"Pesca e Nettarina di Romagna\" PGI, which covers both, and by EUFIC, which gives nectarines the same months as peaches for France and Spain.")}
    for iid, r in rules.items():
        it = I.get(iid)
        if not it:
            continue
        s = it["seasonality"]
        areas = r.get("areas") or {a: list(r["months"]) for a in ("nord", "centro", "sud_isole")}
        s["italy_macro_areas"] = {a: list(v) for a, v in areas.items()}
        s["italy_national"] = list(r.get("national") or r["months"])
        s["derivation_notes"] = {"it": r["note"][0], "en": r["note"][1]}
        s["italy_source"] = {"source": r["source"], "url": r["url"]} if r["url"] else {"source": r["source"]}
        mark_enriched(it, ["seasonality.italy_macro_areas", "seasonality.italy_national"])
        finalize_completeness(it)
        print(iid, "".join({O: ".", P: "p", S: "S", E: "f"}.get(x, "?") for x in s["italy_national"]))
    save_json(DATA / "database.json", db)


if __name__ == "__main__":
    main()

"""Stagionalità italiana per gli alimenti che i calendari di stagione non riportano (2026-11-05). Idempotente.

- Pesca noce: i calendari italiani (WWF, Greenpeace, Altroconsumo, Orto da Coltivare) riportano solo "pesca", senza
  distinguere la pesca noce (nettarina), che è la stessa specie con buccia liscia. Si usa la stagionalità della pesca
  del database, dichiarando la derivazione. Conferme: IGP "Pesca e Nettarina di Romagna" (eAmbrosia) tutela insieme
  pesche e nettarine; EUFIC, dove elenca la nettarina (Francia, Spagna), le dà gli stessi mesi della pesca.
- Tartufi: periodi di raccolta della Legge 16 dicembre 1985, n. 752, art. 6 (data/raw/national_calendars/
  legge_752_1985_art6.html): Tuber magnatum 1 ottobre-31 dicembre; Tuber melanosporum 15 novembre-15 marzo.
  Le regioni possono variare il calendario con ordinanza: è il calendario nazionale. I mesi coperti solo per metà
  sono resi come inizio (primizie) o fine stagione (end_of_season). Raccolta e commercio del fresco sono vietati
  fuori periodo (art. 6), quindi i mesi esterni sono fuori stagione.
- Ovolo buono: Provincia di Cuneo, schede funghi (data/raw/national_calendars/provincia_cuneo_amanita_caesarea.html):
  "presente in estate ed inizio autunno". Resa dichiarata: giugno inizio, luglio-settembre di stagione, ottobre fine.
  Unica fonte istituzionale trovata (Piemonte), applicata a tutte le macro-aree e dichiarata come tale.
Nessun picco (picco solo dove almeno due fonti concordano).
Uso:  python scripts/enrich_special_seasonality.py   (dopo enrich_seasonality.py)
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

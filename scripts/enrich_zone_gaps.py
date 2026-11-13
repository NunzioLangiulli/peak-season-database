"""Fills some missing EUFIC climate zones with national sources cited by EUFIC itself
(https://www.eufic.org/en/page/european-national-sources-to-find-information-on-seasonal-fruit-and-vegetables).

- mountain (Alpine): Gesundheitsportal Österreichs (Austrian Ministry of Health), data/raw/national_calendars/
  austria_gesundheitsportal.json; only for the products listed by the Austrian calendar.
- mediterranean: for products missing from EUFIC in the Mediterranean zone the database's Italian seasonality is used
  (South and Islands macro-area, already verified on Italian sources): Italy is a mainly Mediterranean country and
  for Italy EUFIC refers to a national source (Slow Food). Declared derivation.
The other zones (Atlantic, Continental, Boreal, Pannonian): the gaps mostly concern products not grown
there (citrus, persimmon, loquat, prickly pear…): they stay empty.
Existing EUFIC data are never overwritten. Provenance in seasonality.eufic_zone_sources.
Usage:  python scripts/enrich_zone_gaps.py   (after enrich_seasonality.py)
"""
from common import DATA, RAW, finalize_completeness, load_json, mark_enriched, save_json

AT = {  # id -> Austrian calendar entry
    "bietola_da_coste_swiss_chard": "mangold", "bietola_da_taglio_leaf_beet": "mangold", "indivia_riccia_curly_endive": "endivie",
    "scarola_escarole": "endivie", "cicoria_da_cespo_chicory": "zuckerhut", "fungo_pleurotus_oyster_mushroom": "pilze",
    "fungo_champignon_button_mushroom": "pilze", "radicchio_radicchio": "radicchio", "valerianella_corn_salad": "vogerlsalat",
    "pastinaca_parsnip": "pastinaken", "topinambur_jerusalem_artichoke": "topinambur", "rucola_arugula": "rucola",
    "ribes_redcurrant": "ribisel", "mela_cotogna_quince": "quitten", "sedano_rapa_celeriac": "sellerie",
    "fagiolino_green_bean": "fisolen", "melanzana_eggplant": "melanzani", "mais_corn": "mais",
}
SKIP_MED = {"cece_chickpea", "lenticchia_lentil", "arachide_peanut", "farro_emmer", "orzo_barley", "grano_duro_durum_wheat",
            "riso_rice", "avena_oat", "grano_saraceno_buckwheat", "litchi_lychee", "lime_lime", "maracuja_passion_fruit",
            "banana_banana", "mango_mango", "avocado_avocado", "ananas_pineapple", "papaya_papaya"}
AT_URL = "https://www.gesundheit.gv.at/leben/ernaehrung/saisonkalender.html"


def main():
    at = load_json(RAW / "national_calendars" / "austria_gesundheitsportal.json")["months"]
    db = load_json(DATA / "database.json")
    n_m = n_med = 0
    for it in db["items"]:
        s = it["seasonality"]
        z = s.setdefault("eufic_climatic_zones", {})
        src = s.setdefault("eufic_zone_sources", {})
        ch = []
        k = AT.get(it["id"])
        if k and k in at and not z.get("mountain"):
            z["mountain"] = ["in_season" if m + 1 in at[k] else "out_of_season" for m in range(12)]
            src["mountain"] = {"source": "austria_gesundheitsportal", "url": AT_URL, "entry": k,
                               "note": {"it": "Calendario stagionale del Ministero della salute austriaco (fonte nazionale indicata da EUFIC per l'Austria)",
                                        "en": "Seasonal calendar of the Austrian Ministry of Health (national source listed by EUFIC for Austria)"}}
            ch.append("seasonality.eufic_climatic_zones.mountain")
            n_m += 1
        sud = (s.get("italy_macro_areas") or {}).get("sud_isole")
        if not z.get("mediterranean") and sud and len(sud) == 12 and it["id"] not in SKIP_MED and any(x != "out_of_season" for x in sud):
            z["mediterranean"] = list(sud)
            src["mediterranean"] = {"source": "derived_italy_sud_isole", "entry": "italy_macro_areas.sud_isole",
                                    "note": {"it": "Derivata dalla stagionalità italiana del Sud e Isole (l'Italia è un Paese mediterraneo; EUFIC non riporta l'alimento per questa zona)",
                                             "en": "Derived from Italian seasonality for the South and Islands (Italy is a Mediterranean country; EUFIC does not list this food for the zone)"}}
            ch.append("seasonality.eufic_climatic_zones.mediterranean")
            n_med += 1
        for zz in z:
            if z[zz] and zz not in src:
                src[zz] = {"source": "eufic_map", "url": "https://www.eufic.org/en/explore-seasonal-fruit-and-vegetables-in-europe"}
        for zz in list(src):
            src[zz] = {k: v for k, v in src[zz].items() if v is not None}
        if ch:
            mark_enriched(it, ch)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(f"zona alpina colmata: {n_m}; zona mediterranea derivata: {n_med}")


if __name__ == "__main__":
    main()

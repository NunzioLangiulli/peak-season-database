"""Classe di respirazione secondo la classificazione di Kader (USDA HB66, 'Respiratory Metabolism', Table 1) e
indicatore pratico di deperibilita' per l'app (ripening_and_storage.perishability).

- voce 'exact': la classe della tabella sostituisce quella calcolata (discrepanza se diversa);
- voce 'approx' (es. 'citrus', 'mushroom'): usata solo se la classe manca o e' da verificare;
- prodotti secchi (classe non pertinente): esclusi.
Questo risolve i prodotti sensibili al freddo misurati solo a >=10 °C (pomodoro, banana, peperone, agrumi).
Implicazione pratica (HB66, stesso capitolo): la durata di conservazione varia in modo inverso alla respirazione.
Uso:  python scripts/apply_kader_class.py   (dopo apply_hb66_curated.py e mark_not_applicable.py)
"""
from common import DATA, ROOT, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json

P = "ripening_and_storage.postharvest_physiology.respiration_rate_class"
URL = "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf#page={p}"
LEVEL = ["very_low", "low", "moderate", "high", "very_high", "extremely_high"]
LABEL = {
    "very_low": ("Si conserva a lungo", "Keeps for a long time"),
    "low": ("Si conserva bene", "Keeps well"),
    "moderate": ("Deperibilità media", "Medium perishability"),
    "high": ("Deperibile", "Perishable"),
    "very_high": ("Molto deperibile", "Very perishable"),
    "extremely_high": ("Da consumare subito", "Eat it soon"),
}
TIP = {
    "very_low": ("Respira molto lentamente: è tra i prodotti che durano di più.",
                 "It breathes very slowly: one of the longest-keeping foods."),
    "low": ("Respira lentamente: conservato bene dura a lungo.", "It breathes slowly: stored well, it keeps for a long time."),
    "moderate": ("Respira a ritmo medio: conservalo come indicato e consumalo entro pochi giorni da quando è maturo.",
                 "It breathes at a moderate rate: store it as advised and eat it within a few days of ripening."),
    "high": ("Respira in fretta e perde presto freschezza e sapore: mettilo al fresco appena arrivi a casa e consumalo presto.",
             "It breathes fast and soon loses freshness and flavour: chill it as soon as you get home and eat it soon."),
    "very_high": ("Respira molto in fretta: mettilo subito in frigo e consumalo nel giro di pochi giorni.",
                  "It breathes very fast: refrigerate it straight away and eat it within a few days."),
    "extremely_high": ("Respira velocissimo e consuma in fretta zuccheri e freschezza: mettilo subito in frigo e consumalo entro 1-2 giorni.",
                       "It breathes extremely fast, quickly using up sugars and freshness: refrigerate it immediately and eat it within 1-2 days."),
}


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "kader_respiration_classes.json")
    db = load_json(DATA / "database.json")
    n_set = n_disc = 0
    for it in db["items"]:
        ph = it["ripening_and_storage"]["postharvest_physiology"]
        dc = it["data_completeness"]
        na = P in dc.get("not_applicable_fields", [])
        k = cfg["items"].get(it["id"])
        basis = None
        if k and not na:
            cls, match, entry = k
            pending = P in dc.get("fields_pending_verification", []) or ph["respiration_rate_class"] is None
            if match == "exact" or pending:
                old = ph["respiration_rate_class"]
                if old and old != cls:
                    add_discrepancy(it, P, old, cls, f"USDA HB66, Table 1 'Respiratory Metabolism' (Kader), voce '{entry}'",
                                    "adottata la classe della tabella di Kader")
                    n_disc += 1
                ph["respiration_rate_class"] = cls
                mark_enriched(it, [P])
                n_set += 1
                url = URL.format(p=cfg["page"])
                if url not in it["sources_by_topic"]["other_urls"]:
                    it["sources_by_topic"]["other_urls"].append(url)
                basis = (f"Classe di Kader (USDA HB66, tabella delle classi di respirazione a 5 °C, voce '{entry}'"
                         + (", approssimata" if match == "approx" else "") + ")")
        q = cfg.get("q10_estimates", {}).get(it["id"])
        if q and not na and (P in dc.get("fields_pending_verification", []) or ph["respiration_rate_class"] is None):
            rate, t = q["rate"], q["temp"]
            if t > 10:
                rate /= 2.0 ** ((t - 10) / 10); t = 10
            rate /= 2.5 ** ((t - 5) / 10)
            cls_est = LEVEL[0 if rate < 5 else 1 if rate < 10 else 2 if rate < 20 else 3 if rate < 40 else 4 if rate < 60 else 5]
            if ph["respiration_rate_class"] and ph["respiration_rate_class"] != cls_est:
                add_discrepancy(it, P, ph["respiration_rate_class"], cls_est, f"stima a 5 °C da {q['source']} (Q10 HB66)")
            ph["respiration_rate_class"] = cls_est
            mark_enriched(it, [P])
            basis = (f"Classe stimata: {q['source']} riportato a 5 °C con i Q10 tipici di HB66 (circa {rate:.0f} mg CO2/kg/h); "
                     "prodotto sensibile al freddo, non misurato a 5 °C")
        cls = ph["respiration_rate_class"]
        if cls and not na:
            it["ripening_and_storage"]["perishability"] = {
                "level": LEVEL.index(cls) + 1, "label": {"it": LABEL[cls][0], "en": LABEL[cls][1]},
                "tip": {"it": TIP[cls][0], "en": TIP[cls][1]},
                "basis": basis or "Classe di respirazione a 5 °C da USDA HB66 / UC Davis (valori misurati, vedi note)"}
            mark_enriched(it, ["ripening_and_storage.perishability"])
        elif na:
            it["ripening_and_storage"]["perishability"] = {
                "level": 1, "label": {"it": "Prodotto secco, si conserva a lungo", "en": "Dry product, keeps for a long time"},
                "tip": {"it": "Al fresco, all'asciutto e in un contenitore chiuso.", "en": "Keep cool, dry and in a closed container."},
                "basis": "Prodotto secco: la classe di respirazione non è pertinente; durate da USDA FoodKeeper"}
            mark_enriched(it, ["ripening_and_storage.perishability"])
        else:
            it["ripening_and_storage"]["perishability"] = None
        finalize_completeness(it)
    db["metadata"]["perishability_legend"] = {
        "basis": "Classe di respirazione a 5 °C secondo Kader (USDA HB66, Respiratory Metabolism, Table 1): la durata di conservazione varia in modo inverso alla respirazione.",
        "levels": [{"level": i + 1, "respiration_rate_class": c, "label": {"it": LABEL[c][0], "en": LABEL[c][1]}} for i, c in enumerate(LEVEL)]}
    save_json(DATA / "database.json", db)
    left = [it["id"] for it in db["items"] if P in it["data_completeness"].get("fields_pending_verification", [])
            or (it["ripening_and_storage"]["postharvest_physiology"]["respiration_rate_class"] is None
                and P not in it["data_completeness"].get("not_applicable_fields", []))]
    print(f"classi di Kader applicate: {n_set}, discrepanze: {n_disc}; ancora da verificare: {left}")


if __name__ == "__main__":
    main()

"""Curva stagionale completa per le macro-aree italiane (revisione 2026-11-12, richiesta dell'utente). Idempotente
se applicato all'uscita delle fasi di stagionalità (prima di estimate_zone_gaps.py).

Regole (dichiarate in metadata.seasonality_curve_method e segnate in seasonality.curve_basis):
- Caso 1 - prodotti freschi deperibili (ortaggi da frutto estivi, erbe, piccoli frutti) con mesi di raccolta di Orto
  da Coltivare: la stagionalità si allinea alla raccolta in pieno campo; i mesi di stagione fuori dalla raccolta
  (serra o importazione) diventano fuori stagione, i mesi di raccolta mancanti diventano di stagione.
- Caso 2 - buchi tra due periodi di stagione: un mese isolato fuori stagione si chiude sempre con "fine stagione"
  (artefatto dell'unione dei calendari); due mesi si chiudono se in quel mese il prodotto è di stagione in un'altra
  macro-area italiana (al mercato arriva da lì). Restano le pause reali (PAUSE: rabarbaro e crescione col caldo
  estivo, aglio e pera tra fine scorte e nuovo raccolto).
- Caso 3 - prodotti a raccolta breve e lunga conservazione naturale (fruttaio, cantina, prodotti secchi): raccolta e
  disponibilità restano distinte; seasonality.availability_note spiega all'utente il perché.
- Curva: in ogni periodo continuo di stagione il primo mese è "primizia" e l'ultimo "fine stagione"; il picco sono
  i mesi interni che cadono nei mesi di raccolta in pieno campo (per i prodotti da conservazione: i mesi di raccolta),
  oppure, senza dati di raccolta, il terzo centrale del periodo (almeno 1, al massimo 3 mesi). Periodi di 1 mese:
  picco; di 2 mesi: picco e fine stagione. Disponibilità tutto l'anno senza una raccolta più breve: nessun picco.
- Le curve calcolate dal voto tra calendari con un picco già documentato (almeno due fonti concordi) non si toccano,
  tranne i buchi brevi (caso 2) e i prodotti del caso 1, dove i calendari contano anche serra e importazione.
- Esotici (not_applicable) e prodotti senza stagionalità italiana: invariati.
Uso:  python scripts/apply_seasonality_curve.py   (dopo apply_curated_seasonality.py, prima di estimate_zone_gaps.py)
"""
from common import DATA, finalize_completeness, load_json, mark_enriched, save_json

O, P, S, K, E = "out_of_season", "primizie", "in_season", "peak_season", "end_of_season"
POS = {P, S, K, E}
AREAS = ("nord", "centro", "sud_isole")
AB = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
AB_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CASE1 = {"melanzana_eggplant", "cetriolo_cucumber", "zucchina_zucchini", "pomodoro_tomato", "peperone_bell_pepper",
         "peperoncino_chili_pepper", "fagiolino_green_bean", "basilico_basil", "prezzemolo_parsley", "menta_mint",
         "fragola_strawberry", "lampone_raspberry", "mirtillo_blueberry", "mora_blackberry", "ribes_redcurrant",
         "ribes_nero_blackcurrant", "uva_spina_gooseberry", "gelso_mulberry", "gombo_okra"}
STORAGE = {"aglio_garlic", "cipolla_estiva_summer_onion", "cipolla_invernale_winter_onion", "scalogno_shallot", "patata_potato",
           "patata_dolce_sweet_potato", "zucca_pumpkin", "mela_apple", "pera_pear", "kiwi_kiwifruit", "mela_cotogna_quince",
           "castagna_chestnut", "noce_walnut", "nocciola_hazelnut", "mandorla_almond", "pistacchio_pistachio", "arachide_peanut",
           "farro_emmer", "orzo_barley", "grano_duro_durum_wheat", "riso_rice", "avena_oat", "grano_saraceno_buckwheat",
           "cece_chickpea", "lenticchia_lentil", "cicerchia_grass_pea", "fagiolo_bean", "carruba_carob"}

PAUSE = {"aglio_garlic", "pera_pear", "crescione_watercress", "rabarbaro_rhubarb"}  # pause documentate: restano


def runs(m):
    """Periodi continui di mesi positivi (indici 0-11), anche a cavallo d'anno; None se tutto l'anno."""
    if all(x in POS for x in m):
        return None
    start = next(i for i in range(12) if m[i] not in POS)
    out, cur = [], []
    for k in range(1, 13):
        i = (start + k) % 12
        if m[i] in POS:
            cur.append(i)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def rng(ms, ab):
    ms = sorted(ms)
    return f"{ab[ms[0] - 1]}-{ab[ms[-1] - 1]}" if len(ms) > 1 else ab[ms[0] - 1]


def curve(m, harvest, storage):
    """Assegna primizia, picco e fine stagione a ogni periodo; restituisce la nuova serie."""
    m = list(m)
    rs = runs(m)
    if rs is None:                                   # disponibile tutto l'anno
        hv = sorted(harvest or [])
        if hv and len(hv) < 12:                      # picco = raccolta in pieno campo
            for i in range(12):
                m[i] = K if (i + 1) in hv else S
        return m
    for r in rs:
        for i in r:
            m[i] = S
        if len(r) == 1:
            m[r[0]] = K
            continue
        if len(r) == 2:
            m[r[0]], m[r[1]] = K, E
            continue
        m[r[0]], m[r[-1]] = P, E
        inner = r[1:-1]
        hv = set(harvest or [])
        peak = [i for i in inner if (i + 1) in hv]
        if storage and hv:
            peak = [i for i in r if (i + 1) in hv and i not in (r[0], r[-1])] or peak
        if not peak:
            n = max(1, min(3, round(len(inner) / 3)))
            c = (len(inner) - n) // 2
            peak = inner[c:c + n]
        for i in peak:
            m[i] = K
    return m


def main():
    db = load_json(DATA / "database.json")
    stats = {"case1": 0, "case2_filled": 0, "case3_notes": 0, "curves": 0, "kept_voted_peak": 0}
    for it in db["items"]:
        s, cal = it["seasonality"], it["agricultural_calendar_italy"]
        ita = s.get("italy_macro_areas") or {}
        if not any(ita.get(a) for a in AREAS) or all(x == "not_applicable" for a in AREAS for x in (ita.get(a) or [])):
            continue
        cb = (s.get("curve_basis") or {}).get("it", "")
        voted = it["id"] not in CASE1 and (not cb or cb.startswith("Curva dal voto")) and any(K in (ita.get(a) or []) for a in AREAS)
        stats["kept_voted_peak"] += voted            # picco già documentato dal voto: solo i buchi (caso 2)
        changed = []
        iid = it["id"]
        harvest = {a: sorted((cal.get(a) or {}).get("harvest_months") or []) for a in AREAS}
        # Caso 1: allinea alla raccolta in pieno campo
        if iid in CASE1:
            for a in AREAS:
                m, hv = ita.get(a), harvest[a]
                if m and hv:
                    new = [S if (i + 1) in hv else O for i in range(12)]
                    if new != [S if x in POS else O for x in m]:
                        ita[a] = new
                        changed.append(f"case1:{a}")
            stats["case1"] += bool(changed)
        # Caso 2: buchi brevi colmati se un'altra macro-area è di stagione
        for a in AREAS:
            m = ita.get(a)
            if not m:
                continue
            for i in range(12):
                if m[i] == O and m[(i - 1) % 12] in POS and (m[(i + 1) % 12] in POS or m[(i + 2) % 12] in POS):
                    j = (i + 1) % 12 if m[(i + 1) % 12] == O else None
                    if j is not None and m[(j + 1) % 12] not in POS:
                        continue
                    others = [b for b in AREAS if b != a and ita.get(b) and ita[b][i] in POS]
                    single = j is None and iid not in PAUSE          # pausa di un solo mese: artefatto del merge
                    if single or (others and iid not in STORAGE):
                        m[i] = E
                        stats["case2_filled"] += 1
                        changed.append(f"case2:{a}:{i + 1}")
        # Caso 3: nota sulla disponibilità
        if iid in STORAGE:
            hv = sorted(set().union(*[set(h) for h in harvest.values()]))
            nat = s.get("italy_national") or ita.get("nord") or []
            pos = [i + 1 for i, x in enumerate(nat) if x in POS]
            if hv and pos and len(pos) > len(hv):
                s["availability_note"] = {
                    "it": f"Raccolta in {rng(hv, AB)}; resta di stagione per più mesi grazie alla naturale conservabilità (cantina, fruttaio o prodotto secco), senza serre riscaldate.",
                    "en": f"Harvested in {rng(hv, AB_EN)}; it stays in season for several more months thanks to its natural keeping quality (cellar, fruit store or dried), without heated greenhouses."}
                stats["case3_notes"] += 1
            elif pos:
                s["availability_note"] = {
                    "it": "Si conserva a lungo in modo naturale: è disponibile di stagione per più mesi rispetto alla raccolta.",
                    "en": "It keeps naturally for a long time: it is available in season for longer than its harvest."}
                stats["case3_notes"] += 1
        if voted:
            if changed:
                s["curve_basis"] = {"it": "Curva dal voto tra le fonti; buchi chiusi con la regola del database (metadata.seasonality_curve_method): " + ", ".join(changed),
                                    "en": "Curve from the vote between sources; gaps closed with the database rule (metadata.seasonality_curve_method): " + ", ".join(changed)}
                mark_enriched(it, ["seasonality.italy_macro_areas"])
                finalize_completeness(it)
            continue
        # Curva completa
        for a in AREAS:
            if ita.get(a):
                ita[a] = curve(ita[a], harvest[a], iid in STORAGE)
        if s.get("italy_national"):
            nat_h = sorted(set().union(*[set(h) for h in harvest.values()]))
            s["italy_national"] = curve(s["italy_national"], nat_h, iid in STORAGE)
        stats["curves"] += 1
        if not changed and cb.startswith("Curva completata"):
            continue                                 # già calcolata: la nota con le modifiche resta
        s["curve_basis"] = {"it": "Curva completata con la regola del database (metadata.seasonality_curve_method)" + (": " + ", ".join(changed) if changed else "."),
                            "en": "Curve completed with the database rule (metadata.seasonality_curve_method)" + (": " + ", ".join(changed) if changed else ".")}
        mark_enriched(it, ["seasonality.italy_macro_areas", "seasonality.italy_national"])
        finalize_completeness(it)
    db["metadata"]["seasonality_curve_method"] = {
        "it": "Curva stagionale per le macro-aree italiane (revisione 12/11/2026). In ogni periodo continuo di stagione il primo mese è \"primizia\", "
              "l'ultimo \"fine stagione\"; il picco sono i mesi interni che cadono nella raccolta in pieno campo di Orto da Coltivare (per i prodotti "
              "da conservazione, i mesi di raccolta), altrimenti il terzo centrale del periodo. Periodi di 1 mese: picco; di 2: picco e fine stagione. "
              "Caso 1 (deperibili estivi, erbe, piccoli frutti): stagione allineata alla raccolta in pieno campo. Caso 2: un mese isolato fuori "
              "stagione si chiude con \"fine stagione\"; due mesi si chiudono se un'altra macro-area è di stagione; restano le pause reali "
              "(rabarbaro e crescione d'estate, aglio e pera tra fine scorte e nuovo raccolto). Caso 3 (conservazione naturale): raccolta e "
              "disponibilità distinte, spiegate in availability_note. Le curve con un picco già documentato da almeno due fonti concordi non sono "
              "modificate. Ogni curva calcolata ha curve_basis.",
        "en": "Seasonal curve for the Italian macro-areas (revision 12/11/2026). In each continuous season the first month is \"early season\", the last "
              "\"end of season\"; the peak is the inner months within the open-field harvest of Orto da Coltivare (for storage produce, the harvest "
              "months), otherwise the middle third of the season. 1-month seasons: peak; 2-month: peak and end of season. Case 1 (perishable summer "
              "produce, herbs, small fruits): season aligned with open-field harvest. Case 2: a single off-season month is "
              "closed with \"end of season\"; two months are closed if another macro-area is in season; real pauses remain (rhubarb and "
              "watercress in summer, garlic and pear between the end of stocks and the new harvest). Case 3 (natural storage): harvest and availability kept separate, explained in "
              "availability_note. Curves with a peak already documented by at least two agreeing sources are not changed. Every computed curve "
              "has curve_basis."}
    save_json(DATA / "database.json", db)
    print(stats)


if __name__ == "__main__":
    main()

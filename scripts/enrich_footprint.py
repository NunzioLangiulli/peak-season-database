"""Impronta di carbonio e impronta idrica da SU-EATABLE LIFE (Petersson et al. 2021, Scientific Data 8:127,
DOI 10.1038/s41597-021-00909-8; dataset figshare 13271111, CC BY 4.0), data/raw/su_eatable_life/*.xlsx.

nutrition_and_sustainability.environmental_footprint:
  carbon_kg_co2eq_per_kg, carbon_g_co2eq_per_portion, carbon_reference ('item'/'typology' SEL + incertezza L/H),
  water_l_per_kg, water_l_per_portion, water_reference,
  greenhouse_comparison: CF della stessa coltura in serra (riscaldata '(G)' o non riscaldata '(g)') e rapporto,
  match ('exact' | 'approx'), note.
Valori dalla vita del prodotto fino all'uscita dall'azienda agricola/distribuzione secondo i confini del dataset
(vedi foglio INTRO): indicativi, servono a confrontare alimenti, non a calcolare un bilancio.
Uso:  python scripts/enrich_footprint.py   (dopo enrich_allergens_portions.py, per i valori per porzione)
"""
from common import DATA, RAW, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na
from xlsx_min import read_rows

N = "nutrition_and_sustainability"
F = RAW / "su_eatable_life" / "SuEatableLife_Food_Fooprint_database.xlsx"
URL = "https://doi.org/10.1038/s41597-021-00909-8"


def load(sheet):
    rows = read_rows(F, f"xl/worksheets/{sheet}.xml")
    items, typ = {}, {}
    for x in rows[1:]:
        if len(x) < 7 or not x[1]:
            continue
        try:
            items[x[1].strip()] = (float(x[2]), x[3].strip(), x[4].strip(), x[5].strip())
            typ[x[5].strip()] = float(x[6])
        except ValueError:
            continue
    return items, typ


def load_stats(sheet):
    rows = read_rows(F, f"xl/worksheets/{sheet}.xml")
    out = {}
    for x in rows[2:]:
        if len(x) > 9 and x[3]:
            try:
                out[x[3].strip()] = {"n_values": int(float(x[4])), "min": round(float(x[8]), 2), "max": round(float(x[9]), 2)}
            except ValueError:
                continue
    return out


STATS = {}


def get(ref, items, typ):
    if not ref:
        return None
    kind, name = ref.split(":", 1)
    if kind == "item":
        v = items.get(name)
        if v is None:
            return None
        st = STATS.get(id(items), {}).get(name) or STATS.get(id(items), {}).get(name.rstrip("*").strip()) or {}
        return {"value": v[0], "sel_name": name, "level": "item", "uncertainty": v[1], "sel_note": v[2], "typology": v[3],
                "n_values": st.get("n_values"), "min": st.get("min"), "max": st.get("max")}
    v = typ.get(name)
    return None if v is None else {"value": v, "sel_name": name, "level": "typology", "uncertainty": None, "sel_note": None, "typology": name}


# Soglie di lettura definite per l'app (convenzione dichiarata, non da fonte): servono solo a tradurre i numeri in un
# livello intuitivo. Riferimento di confronto: carne bovina senz'osso, stessa banca dati.
CF_LEVELS = [(0.5, "low"), (1.0, "medium"), (float("inf"), "high")]
WF_LEVELS = [(500, "low"), (1500, "medium"), (float("inf"), "high")]
LEVEL_LABEL = {"low": ("bassa", "low"), "medium": ("media", "medium"), "high": ("alta", "high")}
BEEF = "BEEF BONE FREE MEAT*"


def level(v, scale):
    return None if v is None else next(lab for lim, lab in scale if v < lim)


def rating(it, ef, cf_i, wf_i):
    cf, wf = ef["carbon_kg_co2eq_per_kg"], ef["water_l_per_kg"]
    bc, bw = cf_i[BEEF][0], wf_i[BEEF][0]
    cl, wl = level(cf, CF_LEVELS), level(wf, WF_LEVELS)
    tips_it, tips_en = [], []
    gh = ef.get("greenhouse_comparison")
    if gh and gh.get("times_openfield"):
        kind_it = "in serra riscaldata" if gh["heated"] else "in serra non riscaldata"
        kind_en = "in a heated greenhouse" if gh["heated"] else "in an unheated greenhouse"
        tips_it.append(f"Coltivato {kind_it} (tipico fuori stagione) ha un'impronta di carbonio {str(gh['times_openfield']).replace('.', ',')} volte più alta: sceglilo di stagione e di pieno campo.")
        tips_en.append(f"Grown {kind_en} (typical out of season) its carbon footprint is {gh['times_openfield']:g} times higher: choose it in season and field-grown.")
    ref = (ef.get("carbon_reference") or {}).get("sel_name") or ""
    if "(I)" in ref or "IMPORTED" in ref:
        tips_it.append("Prodotto d'importazione: l'impronta comprende il trasporto fino all'Europa.")
        tips_en.append("Imported product: the footprint includes transport to Europe.")
    if wl == "high":
        tips_it.append("Richiede molta acqua per chilo prodotto: evita gli sprechi e usa tutto ciò che è commestibile.")
        tips_en.append("It takes a lot of water per kilo: avoid waste and use every edible part.")
    return {
        "carbon_level": cl, "water_level": wl,
        "carbon_label": {"it": f"Impronta di carbonio {LEVEL_LABEL[cl][0]}", "en": f"{LEVEL_LABEL[cl][1].capitalize()} carbon footprint"} if cl else None,
        "water_label": {"it": f"Impronta idrica {LEVEL_LABEL[wl][0]}", "en": f"{LEVEL_LABEL[wl][1].capitalize()} water footprint"} if wl else None,
        "times_lower_than_beef_carbon": round(bc / cf) if cf else None,
        "times_lower_than_beef_water": round(bw / wf) if wf else None,
        "tips": {"it": " ".join(tips_it), "en": " ".join(tips_en)} if tips_it else None,
        "basis": ("Livelli: carbonio basso < 0,5, medio 0,5-1, alto > 1 kg CO2eq/kg; acqua bassa < 500, media 500-1500, alta > 1500 L/kg "
                  "(soglie di lettura definite per l'app). Confronto con 'BEEF BONE FREE MEAT' SU-EATABLE LIFE "
                  f"({bc:.1f} kg CO2eq/kg, {bw:.0f} L/kg).")}


AGB_FILE = RAW / "agribalyse" / "agribalyse_synthese.csv"
AGB_URL = "https://data.ademe.fr/datasets/agribalyse-31-synthese"
# erbe fresche assenti in SU-EATABLE LIFE -> AGRIBALYSE 3.1 (ADEME), solo carbonio, confini diversi (fino al consumo)
AGB_MAP = {"basilico_basil": "11033", "menta_mint": "11027", "origano_oregano": "11035", "prezzemolo_parsley": "11014",
           "rosmarino_rosemary": "11068", "salvia_sage": "11069", "timo_thyme": "11070"}
_AGB = {}


def agb_ref(code):
    if not _AGB:
        import csv
        with open(AGB_FILE, encoding="utf-8-sig") as fh:
            rd = csv.reader(fh)
            next(rd)
            for x in rd:
                _AGB[x[0]] = x
    x = _AGB[code]
    return {"value": float(x[13]), "sel_name": x[5], "level": "item", "source": "agribalyse", "agribalyse_code": code,
            "dqr": float(x[11]),
            "boundary": {"it": "AGRIBALYSE: dal campo al consumo (include imballaggio, trasporto e distribuzione in Francia), non direttamente confrontabile con i valori SU-EATABLE LIFE",
                         "en": "AGRIBALYSE: from field to consumer (includes packaging, transport and retail in France), not directly comparable with SU-EATABLE LIFE values"}}


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "sel_footprint_map.json")["items"]
    cf_i, cf_t = load("sheet2")
    wf_i, wf_t = load("sheet7")
    STATS[id(cf_i)] = load_stats("sheet4")
    STATS[id(wf_i)] = load_stats("sheet9")
    db = load_json(DATA / "database.json")
    n_cf = n_wf = 0
    missing = []
    for it in db["items"]:
        n = it[N]
        m = cfg.get(it["id"])
        portion = (n.get("reference_portion") or {}).get("grams")
        P = f"{N}.environmental_footprint"
        agb = AGB_MAP.get(it["id"])
        if not m and agb:
            m = [None, None, "approx"]
        if not m:
            n["environmental_footprint"] = None
            if it["id"] in ("fungo_porcino_porcini_mushroom", "fungo_ovolo_caesars_mushroom", "tartufo_nero_black_truffle", "tartufo_bianco_white_truffle",
                            "finferlo_chanterelle", "spugnola_morel", "asparago_selvatico_wild_asparagus", "lampascioni_tassel_hyacinth"):  # raccolta spontanea
                set_na(it, [P])  # raccolta spontanea: nessuna coltivazione di riferimento
            missing.append(it["id"])
            finalize_completeness(it)
            continue
        cf, wf = get(m[0], cf_i, cf_t), get(m[1], wf_i, wf_t)
        if cf is None and agb:
            cf = agb_ref(agb)
        gh = get(m[3], cf_i, cf_t) if len(m) > 3 else None
        ef = {
            "carbon_kg_co2eq_per_kg": round(cf["value"], 2) if cf else None,
            "carbon_g_co2eq_per_portion": round(cf["value"] * portion) if cf and portion else None,
            "carbon_reference": cf,
            "water_l_per_kg": round(wf["value"]) if wf else None,
            "water_l_per_portion": round(wf["value"] * portion / 1000) if wf and portion else None,
            "water_reference": wf,
            "greenhouse_comparison": ({"carbon_kg_co2eq_per_kg": round(gh["value"], 2), "sel_name": gh["sel_name"],
                                       "heated": "(G)" in gh["sel_name"],
                                       "times_openfield": round(gh["value"] / cf["value"], 1) if cf else None} if gh else None),
            "match": m[2], "source": AGB_URL if (cf and cf.get("source") == "agribalyse" and not wf) else URL}
        ef["sustainability_rating"] = {k: v for k, v in rating(it, ef, cf_i, wf_i).items() if v is not None}
        for ref in ("carbon_reference", "water_reference"):
            if ef[ref]:
                ef[ref] = {k: v for k, v in ef[ref].items() if v is not None}
        n["environmental_footprint"] = ef
        na = [f"{P}.{k}" for k, v in ef.items() if v is None]
        if na:
            set_na(it, na)
        mark_enriched(it, [P])
        if URL not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append(URL)
        n_cf += bool(cf)
        n_wf += bool(wf)
        finalize_completeness(it)
    db["metadata"]["environmental_footprint_method"] = {
        "it": "Impronta di carbonio (kg CO2eq per kg di prodotto) e impronta idrica (litri d'acqua per kg) dal database SU-EATABLE LIFE "
              "(progetto LIFE UE, Petersson et al. 2021, CC BY 4.0). Valori medi armonizzati da letteratura: utili per confrontare "
              "alimenti e modalità di coltivazione (pieno campo, serra riscaldata, importazione), non come dato di un singolo prodotto.",
        "en": "Carbon footprint (kg CO2eq per kg) and water footprint (litres per kg) from the SU-EATABLE LIFE database (EU LIFE project, "
              "Petersson et al. 2021, CC BY 4.0). Harmonised literature averages: meant to compare foods and production modes "
              "(open field, heated greenhouse, imported), not as values for a specific product.",
        "source": URL, "dataset": "https://figshare.com/articles/dataset/13271111"}
    save_json(DATA / "database.json", db)
    print(f"carbonio: {n_cf}, acqua: {n_wf}; senza voce: {missing}")


if __name__ == "__main__":
    main()

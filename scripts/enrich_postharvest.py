"""Step 1.3d - Postharvest physiology and ethylene (USDA ARS Handbook 66 + UC Davis Produce Fact Sheets).

Sources:
- data/raw/usda_hb66.txt (text of the PDF, downloaded by scripts/... see fetch in this file): chapter per product
  ("Optimum Storage Conditions", "Chilling Sensitivity", "Ethylene Production and Sensitivity") and Table 1
  (respiration at 0-25 °C, ethylene production).
- data/raw/ucdavis_extract.json (read with the browser): temperature, RH, ethylene production and response, chilling.
Classes (Kader A.A., Postharvest Technology of Horticultural Crops, UC ANR 2002, used by UC Davis):
- respiration at 5 °C (mg CO2/kg·h): <5 very_low, 5-10 low, 10-20 moderate, 20-40 high, 40-60 very_high, >60 extremely_high
- ethylene at 20 °C (µL/kg·h): <0.1 very_low, 0.1-1 low, 1-10 moderate, 10-100 high, >100 very_high
keep_away_from = database products with high/very_high ethylene production, for sensitive products.

Usage:  python scripts/enrich_postharvest.py
"""
import re

import pymupdf

from common import (CONFIG, DATA, RAW, add_discrepancy, finalize_completeness, http_get, iter_blocks, load_json,
                    mark_enriched, save_json)

HB66_URL = "https://www.ars.usda.gov/is/np/commercialstorage/commercialstorage.pdf"
HEADINGS = ["Scientific Name", "Quality Characteristics", "Horticultural Maturity", "Grades, Sizes", "Precooling",
            "Optimum Storage Conditions", "Storage Conditions", "Controlled Atmosphere", "Retail Outlet", "Chilling Sensitivity",
            "Ethylene Production", "Respiration Rates", "Physiological Disorders", "Postharvest Pathology", "Quarantine",
            "Suitability as Fresh-Cut", "Special Considerations", "References", "Acknowledgments", "Freezing"]

MAP = {  # id -> (HB66 chapter title, Table 1 key, quality)
    "aglio_garlic": ("Garlic", "Garlic", "exact"), "asparago_asparagus": ("Asparagus", "Asparagus", "exact"),
    "carciofo_artichoke": ("Artichoke", "Artichoke", "exact"), "carota_carrot": ("Carrot", "Carrot", "exact"),
    "barbabietola_beetroot": ("Beet", "Beets", "exact"), "bietola_da_coste_swiss_chard": ("Swiss Chard", "Swiss chard", "exact"),
    "bietola_da_taglio_leaf_beet": ("Swiss Chard", "Swiss chard", "approx"),
    "cavoletto_di_bruxelles_brussels_sprout": ("Brussels Sprouts", "Brussels sprouts", "exact"),
    "cavolfiore_cauliflower": ("Cauliflower", "Cauliflower", "exact"), "broccolo_broccoli": ("Broccoli", "Broccoli", "exact"),
    "cavolo_cappuccio_cabbage": ("Cabbage", "Cabbage", "exact"), "cavolo_nero_black_kale": ("Greens for Cooking", "Kale", "approx"),
    "cavolo_rapa_kohlrabi": ("Kohlrabi", "Kohlrabi", "exact"), "cavolo_verza_savoy_cabbage": ("Cabbage", "Cabbage", "approx"),
    "cetriolo_cucumber": ("Cucumber", "Cucumber", "exact"), "cicoria_da_cespo_chicory": ("Endive and Escarole", "Endive", "approx"),
    "cicoria_da_taglio_cutting_chicory": ("Endive and Escarole", "Endive", "approx"),
    "cima_di_rapa_turnip_greens": ("Greens for Cooking", "Turnip greens", "approx"),
    "cipolla_estiva_summer_onion": ("Onion", "Onion", "exact"), "cipolla_invernale_winter_onion": ("Onion", "Onion", "exact"),
    "fagiolo_bean": ("Bean", "Beans", "approx"), "fagiolino_green_bean": ("Bean", "Beans", "exact"),
    "fava_broad_bean": ("Bean", "Beans", "approx"), "finocchio_fennel": ("Fennel", "Fennel", "exact"),
    "lattuga_da_cespo_head_lettuce": ("Lettuce", "Lettuce", "exact"), "lattuga_da_taglio_leaf_lettuce": ("Lettuce", "Lettuce", "exact"),
    "melanzana_eggplant": ("Eggplant", "Eggplant", "exact"), "pastinaca_parsnip": ("Parsnip", "Parsnip", "exact"),
    "patata_potato": ("Potato", "Potato", "exact"), "peperone_bell_pepper": ("Pepper", "Pepper", "exact"),
    "pomodoro_tomato": ("Tomato", "Tomato", "exact"), "porro_leek": ("Leek", "Leek", "exact"),
    "radicchio_radicchio": ("Radicchio", "Radicchio", "exact"), "rapa_turnip": ("Turnip", "Turnip", "exact"),
    "ravanello_radish": ("Radish", "Radish", "exact"), "scalogno_shallot": ("Onion", "Onion", "approx"),
    "sedano_celery": ("Celery", "Celery", "exact"), "spinacio_spinach": ("Greens for Cooking", "Spinach", "approx"),
    "topinambur_jerusalem_artichoke": ("Jerusalem Artichoke", "Jerusalem artichoke", "exact"),
    "zucca_pumpkin": ("Pumpkin and Winter Squash", "Pumpkin", "exact"), "zucchina_zucchini": ("Squash", "Squash", "exact"),
    "arachide_peanut": ("Peanut", None, "exact"), "anguria_watermelon": ("Watermelon", "Watermelon", "exact"),
    "melone_melon": ("Netted Melon", "Melon", "exact"), "albicocca_apricot": ("Apricot", "Apricot", "exact"),
    "arancia_orange": ("Orange", "Orange", "exact"), "cachi_persimmon": ("Persimmon", "Persimmon", "exact"),
    "ciliegia_cherry": ("Cherry (Sweet)", "Cherry", "exact"), "clementine_clementine": ("Mandarin (Tangerine)", "Mandarin", "approx"),
    "fico_fig": ("Fig", "Fig", "exact"), "fragola_strawberry": ("Strawberry", "Strawberry", "exact"),
    "kiwi_kiwifruit": ("Kiwifruit", "Kiwifruit", "exact"), "lampone_raspberry": ("Raspberry", "Raspberry", "exact"),
    "limone_lemon": ("Lemon", "Lemon", "exact"), "mandarino_mandarin": ("Mandarin (Tangerine)", "Mandarin", "exact"),
    "mela_apple": ("Apple", "Apple", "exact"), "melograno_pomegranate": ("Pomegranate", "Pomegranate", "exact"),
    "mirtillo_blueberry": ("Blueberry", "Blueberry", "exact"), "mora_blackberry": ("Blackberry", "Blackberry", "exact"),
    "pera_pear": ("Pear", "Pear", "exact"), "pesca_peach": ("Peach", "Peach", "exact"),
    "susina_plum": ("Plum and Fresh Prune", "Plum", "exact"), "uva_table_grape": ("Grape (Table)", "Grape", "exact"),
    "banana_banana": ("Banana and Plantain", "Banana", "exact"), "mango_mango": ("Mango", "Mango", "exact"),
    "avocado_avocado": ("Avocado", "Avocado", "exact"), "prezzemolo_parsley": ("Parsley", "Parsley", "exact"),
    "fungo_champignon_button_mushroom": ("Mushroom", "Mushroom", "exact"),
    "fungo_pleurotus_oyster_mushroom": ("Mushroom", "Mushroom", "approx"), "mais_corn": ("Sweet Corn", "Sweet corn", "exact"),
    "cavolo_rosso_red_cabbage": ("Cabbage", "Cabbage", "approx"), "sedano_rapa_celeriac": ("Celeriac", "Celeriac", "exact"),
    "indivia_belga_belgian_endive": ("Chicory (Belgian Endive or Witloof", "Chicory", "exact"),
    "scarola_escarole": ("Endive and Escarole", "Endive", "exact"), "indivia_riccia_curly_endive": ("Endive and Escarole", "Endive", "exact"),
    "nespola_loquat": ("Loquat", "Loquat", "exact"), "pompelmo_grapefruit": ("Grapefruit", "Grapefruit", "exact"),
    "mela_cotogna_quince": ("Quince", "Quince", "exact"), "ribes_redcurrant": ("Currant, Gooseberry, and Elderberry", "Currant", "exact"),
    "pesca_noce_nectarine": ("Nectarine", "Nectarine", "exact"), "fico_d_india_prickly_pear": ("Prickly Pear", "Prickly pear", "exact"),
    "litchi_lychee": ("Litchi", "Litchi", "exact"), "lime_lime": ("Lime", "Lime", "exact"),
    "ananas_pineapple": ("Pineapple", "Pineapple", "exact"), "papaya_papaya": ("Papaya", "Papaya", "exact"),
    "maracuja_passion_fruit": ("Passion Fruit", "Passion fruit", "exact"), "tartufo_nero_black_truffle": ("Truffle", "Truffle", "exact"), "tartufo_bianco_white_truffle": ("Truffle", "Truffle", "exact"),
    "basilico_basil": (None, "Basil", "exact"), "castagna_chestnut": (None, None, None),
}
# products added on 2026-11-05 (config/new_items_2026_11_05.json): HB66 chapter, Table 1 entry, quality
MAP.update({k: tuple(v["hb66"]) for k, v in load_json(CONFIG / "new_items_2026_11_05.json").items() if v.get("hb66")})


def rclass(v):
    if v is None:
        return None
    return "very_low" if v < 5 else "low" if v < 10 else "moderate" if v < 20 else "high" if v < 40 else "very_high" if v < 60 else "extremely_high"


def eclass(v):
    if v is None:
        return None
    return "very_low" if v < 0.1 else "low" if v <= 1 else "moderate" if v <= 10 else "high" if v <= 100 else "very_high"


def load_hb66():
    txt = RAW / "usda_hb66.txt"
    if not txt.exists():
        pdf = RAW / "usda_hb66.pdf"
        if not pdf.exists():
            pdf.write_bytes(http_get(HB66_URL, timeout=180).content)
        doc = pymupdf.open(pdf)
        txt.write_text("\n\f".join(f"===PAGE {i + 1}===\n{p.get_text()}" for i, p in enumerate(doc)), encoding="utf-8")
    pages = txt.read_text(encoding="utf-8").split("\n\f")
    chapters = []
    for i, p in enumerate(pages):
        if "Scientific Name and Introduction" in p:
            head = [ln.strip() for ln in p.split("Scientific Name and Introduction")[0].splitlines()
                    if ln.strip() and not ln.startswith("===")]
            if len(head) >= 2:
                chapters.append((head[1], i))
    chap = {}
    for k, (title, start) in enumerate(chapters):
        end = chapters[k + 1][1] if k + 1 < len(chapters) else start + 6
        body = "\n".join(pages[start:end])
        chap[title] = {"page": start + 1, "text": body}
    # Table 1 (pages 17-22 roughly): name followed by 6 respiration values and the ethylene value
    table = {}
    tt = "\n".join(pages[16:23])
    tt = tt[tt.find("Table 1. Rates of respiration"):]
    # tokens with an indent marker: in the extracted text the sub-rows (e.g. Apple -> Fall/Summer) are
    # preceded by a line containing only a tab
    toks, indent = [], False
    for line in tt.split("\n"):
        if line.strip() == "":
            indent = indent or ("\t" in line)
            continue
        for k, part in enumerate(p for p in line.split("\t") if p.strip()):
            toks.append((part.strip(), indent and k == 0))
        indent = False
    i, parent = 0, None
    isval = lambda v: re.match(r"^(nd\d?|\d+(\.\d+)?)$", v)  # noqa: E731
    while i < len(toks):
        t, ind = toks[i]
        vals = [x[0] for x in toks[i + 1:i + 7]]
        if re.match(r"^[A-Z][A-Za-z ,'()\-/]+?\d?$", t) and len(vals) == 6 and all(isval(v) for v in vals):
            name = re.sub(r"\d+$", "", t).strip()
            eth = toks[i + 7][0] if i + 7 < len(toks) else None
            key = f"{parent} ({name})" if ind and parent else name
            if not ind:
                parent = None
            table.setdefault(key, {"resp": [None if v.startswith("nd") else float(v) for v in vals], "eth": eth})
            i += 8
            continue
        if re.match(r"^[A-Z][A-Za-z ,'\-]+\d?$", t) and not ind:
            parent = re.sub(r"\d+$", "", t).strip()      # riga "genitore" senza valori propri
        i += 1
    return chap, table


def table_lookup(table, key):
    if not key:
        return None
    k = key.lower()
    for name in table:
        if name.lower() == k:
            return table[name]
    for name in table:
        n = name.lower()
        if n.startswith(k + " (") or n.startswith(k + ",") or n.startswith(k + "/") or n.startswith(k + " "):
            return table[name]
    return None


def eth_word(text):
    if not text:
        return None
    # only the sentences about ethylene PRODUCTION (not sensitivity or respiration)
    sents = [s for s in re.split(r"(?<=\.)\s", text.lower()) if "ethylene" in s and re.search(r"produc|evolution|emit", s)]
    for s in sents:
        for pat, cls in ((r"very high|extremely high|copious", "very_high"), (r"\bhigh\b|large amounts|large quantities", "high"),
                         (r"\bmoderate\b", "moderate"), (r"very low|very little|only very low|negligible|trace", "very_low"),
                         (r"\blow\b|little|small amounts", "low")):
            if re.search(pat, s):
                return cls
    return None


def section(text, name):
    i = text.find(name)
    if i < 0:
        return None
    rest = text[i + len(name):]
    nxt = min([rest.find("\n" + h) for h in HEADINGS if rest.find("\n" + h) > 0] or [len(rest)])
    return re.sub(r"\s+", " ", rest[:nxt]).strip()


def best_sentence(text, keys):
    """First sentence of the text containing one of the keywords (e.g. 'recommended', 'optimum')."""
    if not text:
        return None
    for s in re.split(r"(?<=[.;])\s+", text):
        if any(k in s.lower() for k in keys):
            return s
    return None


def num_range(s, unit_pat):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:°C)?\s*(?:to|-|–)\s*(-?\d+(?:\.\d+)?)\s*" + unit_pat, s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return {"min": min(a, b), "max": max(a, b)}
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*" + unit_pat, s)
    if m:
        a = float(m.group(1))
        return {"min": a, "max": a}
    return None


def rh_range(s):
    if not s:
        return None
    m = re.search(r"(\d+)\s*(?:to|-|–)\s*(\d+)\s*%", s)
    if m:
        return {"min": int(m.group(1)), "max": int(m.group(2))}
    m = re.search(r">\s*(\d+)\s*%", s)
    if m:
        return {"min": int(m.group(1)), "max": 100}
    m = re.search(r"(\d+)\s*%", s)
    return {"min": int(m.group(1)), "max": int(m.group(1))} if m else None


HINT = {  # HB66 chapters covering several product types: sentence to use for the product
    "cipolla_estiva_summer_onion": "dry onion", "cipolla_invernale_winter_onion": "dry onion", "scalogno_shallot": "dry onion",
    "fagiolino_green_bean": "snap", "lattuga_da_cespo_head_lettuce": "crisphead", "lattuga_da_taglio_leaf_lettuce": "leaf",
}


def life_days(s):
    unit = r"(day|week|wk|month|mo)s?\b"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*" + unit, s) or \
        re.search(r"(\d+(?:\.\d+)?)()\s*" + unit, s)
    if not m:
        return None
    f = {"day": 1, "week": 7, "wk": 7, "month": 30, "mo": 30}[m.group(3)]
    a = float(m.group(1)) * f
    b = float(m.group(2)) * f if m.group(2) else a
    return [round(a), round(b)]


def sens_from_text(s):
    if not s:
        return None
    s = s.lower()
    # harmful effects described (even at low concentrations) -> sensitive
    positive = re.search(r"(extremely|highly|very|moderately) sensitive|sensitive to (physiological|exogenous|ethylene)[^.]{0,40}as low as|"
                         r"as low as|promot\w+ (chlorophyll|yellowing|browning)|stimulat\w* (the )?growth of botrytis|botrytis[^.]{0,60}stimulated|stimulation of botrytis|"
                         r"accelerat\w+ (yellowing|softening|ripening|decay|the lignification|deterioration)|adversely|"
                         r"respond to (exogenous |wound- ?induced )?[^.]{0,30}ethylene with|causes? (leaf |loss|brown|russet|yellow|abscission)|"
                         r"hastens? ripening|induce\w* (fruit )?softening|are (very )?sensitive to ethylene", s)
    negative = re.search(r"not (particularly |very |significantly )?(sensitive|affected|impacted)|insensitive|low sensitivity|"
                         r"sensitivity to ethylene is (also )?low|do(es)? not respond|not considered|respond very little|minimal", s)
    if positive:
        return True
    if negative:
        return False
    return None


def chill_from_text(s):
    if not s:
        return None, None
    low = s.lower()
    if re.search(r"not (sensitive|susceptible) to chilling|not (known to be )?chilling[- ]sensitive|are not sensitive to chilling|"
                 r"not subject to chilling|not (known to be )?sensitive to chilling", low):
        return False, None
    if "chilling" in low:
        m = re.search(r"(?:below|under|lower than)\s*(-?\d+(?:\.\d+)?)\s*°C", s)
        return True, float(m.group(1)) if m else None
    return None, None


def eth_value(s):
    if not s:
        return None
    s = s.lower()
    if "very low" in s:
        return 0.05
    m = re.search(r"([<>])?\s*(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    v = float(m.group(2))
    # "<x" is an upper bound: half of it is used (central value of the possible range), so "<1.1" (cabbage) stays
    # in the low class instead of moving to "moderate" (fix 2026-11-06)
    return v * 0.5 if m.group(1) == "<" else v * 1.01 if m.group(1) == ">" else v


def main():
    db = load_json(DATA / "database.json")
    idx = {i["id"]: i for i in load_json(DATA / "items_index.json")["items"]}
    ucd = load_json(RAW / "ucdavis_extract.json")["sheets"]
    chap, table = load_hb66()
    save_json(RAW / "usda_hb66_table1.json", table)
    eth_cls = {}
    stats = {"hb66": 0, "ucd": 0, "none": []}

    for b, block in iter_blocks(db["items"], 15):
        for it in block:
            iid = it["id"]
            rs = it["ripening_and_storage"]
            ph, eth = rs["postharvest_physiology"], rs["ethylene_compatibility"]
            title, tkey, q = MAP.get(iid, (None, None, None))
            ch = next((v for k, v in chap.items() if title and k.startswith(title)), None)
            u = ucd.get((idx[iid]["sources"].get("uc_davis") or {}).get("slug"))
            trow = table_lookup(table, tkey)
            if not ch and not u and not trow:
                stats["none"].append(iid)
                finalize_completeness(it)
                continue
            enr, used = [], []
            new = {}
            if ch:
                used.append(f"USDA HB66 p.{ch['page']} ({title}{', approssimato' if q == 'approx' else ''})")
                st = section(ch["text"], "Optimum Storage Conditions") or section(ch["text"], "Storage Conditions") or ""
                hint = HINT.get(iid)
                sents = [s for s in re.split(r"(?<=[.;])\s+", st)
                         if not re.search(r"freezing point|curing|cured|half as long|only \d|decreas|shorter|reduced to|higher temperatures", s.lower())]
                if hint:
                    sents = [s for s in sents if hint in s.lower()] or sents
                has_t = lambda s: re.search(r"(at|is|of)\s+-?\d+(\.\d+)?\s*(°C|ºC|to|±)", s)  # noqa: E731
                ts = next((s for s in sents if re.search(r"optimum|optimal|recommend|ideal", s.lower()) and has_t(s)), None) or \
                     next((s for s in sents if re.search(r"stored|storage|storing|kept|maintain|held", s.lower()) and has_t(s)), None)
                new["temp"] = num_range(ts, r"°C") if ts else None
                rs = next((s for s in sents if re.search(r"\d+\s*%\s*rh|% relative humidity|rh (of|should)|\d+%\s*rh", s.lower())), None)
                new["rh"] = rh_range(rs) if rs else None
                ls = next((s for s in sents if re.search(r"storage life|can be kept|kept for|can be stored|stored for|keep for|last", s.lower())
                           and re.search(r"\d+\s*(day|week|wk|mo|month)", s.lower())), None)
                new["life"] = life_days(ls) if ls else None
                fz = re.search(r"freez\w*[^.]{0,60}?(-\d+(?:\.\d+)?)\s*°C", ch["text"])
                new["freeze"] = float(fz.group(1)) if fz else None
                cs = section(ch["text"], "Chilling Sensitivity")
                new["chill"], new["chill_t"] = chill_from_text(cs)
                es = section(ch["text"], "Ethylene Production and Sensitivity") or section(ch["text"], "Ethylene Production")
                new["sens"] = sens_from_text(es)
                new["eth_word"] = eth_word(es)
                stats["hb66"] += 1
            if u:
                used.append(f"UC Davis {idx[iid]['sources']['uc_davis']['slug']}")
                # UC Davis has explicit "Optimum Temperature/Relative Humidity" fields: they take precedence over the
                # HB66 paragraph, where the first figure may refer to other conditions (e.g. garlic 20-30 °C for curing)
                tt = u.get("T") or ""
                if re.match(r"^\s*(-?\d|[A-Za-z ]{0,20}:\s*-?\d)", tt):
                    ut = num_range(tt.split("(")[0], r"°C")
                elif re.search(r"(storage|store|storing|stored)[^.]{0,40}\b(at|is)\s+-?\d", tt.lower()):
                    ut = num_range(re.split(r"\(", re.search(r"\b(?:at|is)\s+(-?\d[^(]*)", tt).group(1))[0], r"°C")
                else:
                    ut = None
                if ut:
                    if new.get("temp") and new["temp"] != ut:
                        it["data_completeness"]["notes"] += f" Temperatura: HB66 {new['temp']} vs UC Davis {ut} (adottata UC Davis, campo 'Optimum Temperature')."
                    new["temp"] = ut
                elif not new.get("temp"):
                    new["temp"] = num_range(u.get("T") or "", r"°C")
                ur = rh_range(u.get("RH")) if re.match(r"^\s*[>\d]", u.get("RH") or "") else None
                if ur:
                    new["rh"] = ur
                elif not new.get("rh"):
                    new["rh"] = rh_range(u.get("RH"))
                if new.get("sens") is None:
                    new["sens"] = sens_from_text(u.get("ER"))
                if new.get("chill") is None and u.get("CI"):
                    new["chill"], ct = chill_from_text(u["CI"])
                    new["chill_t"] = new.get("chill_t") or ct
                new["ucd_eth"] = eth_value(u.get("EP")) if u.get("EP") and re.search(r"\d|very low", u["EP"].lower()) and not u["EP"].startswith("Temperature") else None
                stats["ucd"] += 1
            if trow:
                tr = trow
                used.append(f"USDA HB66 Tabella 1 ({tkey})")
                new["resp5"] = tr["resp"][1]
                new["eth20"] = eth_value(tr["eth"]) if tr["eth"] and not tr["eth"].lower().startswith("varies") else None
            # --- scrittura
            def put(path, obj, key, val, draft_cmp=True):
                if val is None:
                    return
                old = obj.get(key)
                if draft_cmp and old is not None and old != val:
                    add_discrepancy(it, path, old, val, "; ".join(used))
                obj[key] = val
                enr.append(path)
            P = "ripening_and_storage.postharvest_physiology"
            put(f"{P}.optimal_temperature_c", ph, "optimal_temperature_c", new.get("temp"))
            put(f"{P}.optimal_humidity_percent", ph, "optimal_humidity_percent", new.get("rh"))
            put(f"{P}.freezing_point_c", ph, "freezing_point_c", new.get("freeze"), False)
            put(f"{P}.respiration_rate_class", ph, "respiration_rate_class", rclass(new.get("resp5")))
            if new.get("life"):
                put(f"{P}.estimated_shelf_life_days.refrigerated_days", ph["estimated_shelf_life_days"], "refrigerated_days", new["life"])
            if new.get("chill") is not None:
                put(f"{P}.chilling_injury.susceptible", ph["chilling_injury"], "susceptible", new["chill"])
                if new["chill"] is False and ph["chilling_injury"]["critical_temperature_c"] not in (None,) and ph["chilling_injury"]["critical_temperature_c"] > 0:
                    ph["chilling_injury"]["critical_temperature_c"] = None   # draft threshold inconsistent with "not sensitive"
                if new.get("chill_t") is not None:
                    put(f"{P}.chilling_injury.critical_temperature_c", ph["chilling_injury"], "critical_temperature_c", new["chill_t"])
            ev = new.get("eth20") if new.get("eth20") is not None else new.get("ucd_eth")
            ec = eclass(ev) if ev is not None else new.get("eth_word")
            E = "ripening_and_storage.ethylene_compatibility"
            if ec:
                put(f"{E}.ethylene_production_class", eth, "ethylene_production_class", ec, False)
                put(f"{E}.produces_ethylene", eth, "produces_ethylene", ec in ("moderate", "high", "very_high", "extremely_high"))
                eth_cls[iid] = ec
            if new.get("sens") is not None:
                put(f"{E}.sensitive_to_ethylene", eth, "sensitive_to_ethylene", new["sens"])
            if used:
                if ch:
                    urls = it["sources_by_topic"]["postharvest_ucdavis_usda_url"]
                    if HB66_URL not in urls:
                        urls.append(HB66_URL)
                it["data_completeness"]["notes"] += " Post-raccolta: " + "; ".join(used) + "."
            mark_enriched(it, enr)
        save_json(DATA / "database.json", db)
        print(f"blocco {b} salvato")

    # correzioni manuali verificate
    ov = load_json(CONFIG / "postharvest_overrides.json")["items"]
    for it in db["items"]:
        for k, v in ov.get(it["id"], {}).items():
            if k != "source":
                it["ripening_and_storage"]["postharvest_physiology"][k] = v
                it["data_completeness"]["notes"] += f" {k} corretto manualmente: {ov[it['id']]['source']}."
    # keep_away_from (after classifying all of them)
    producers = sorted(i for i, c in eth_cls.items() if c in ("high", "very_high", "extremely_high"))
    for it in db["items"]:
        eth = it["ripening_and_storage"]["ethylene_compatibility"]
        if eth["sensitive_to_ethylene"] is True:
            new = [p for p in producers if p != it["id"]]
            if sorted(eth["keep_away_from"]) != new:
                add_discrepancy(it, "ripening_and_storage.ethylene_compatibility.keep_away_from", eth["keep_away_from"], new,
                                "calcolato: alimenti del database con produzione di etilene high/very_high (USDA HB66 / UC Davis)")
            eth["keep_away_from"] = new
            mark_enriched(it, ["ripening_and_storage.ethylene_compatibility.keep_away_from"])
        elif eth["sensitive_to_ethylene"] is False:
            eth["keep_away_from"] = []
        finalize_completeness(it)
    db["metadata"]["postharvest_method"] = {"it": __doc__.split("Classi")[1].split("Uso:")[0].strip(), "producers_high": producers}
    save_json(DATA / "database.json", db)
    print(stats, "produttori high/very_high:", producers)


if __name__ == "__main__":
    main()

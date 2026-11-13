"""Checks the PDO/PGI designations against the EU eAmbrosia register (data/raw/eambrosia_it.json).

- Draft designations found in the register -> confirmed (official name and type).
- Draft designations NOT found -> removed from the database, saved in draft_legacy_values.json and flagged
  as a discrepancy.
- Register designations (class 1.6 fruit, vegetables and cereals, status "Registrata") whose name contains the
  product name -> added.
Usage:  python scripts/verify_dop_igp.py
"""
import re
import unicodedata

from common import CONFIG, DATA, RAW, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json

# keywords (start of word) per product; exclusions to avoid wrong matches
EXCLUDE = {"fico_fig": ["india"], "mela_apple": ["cotogn", "melanzan"], "pesca_peach": ["noce"], "cipolla_estiva_summer_onion": [],
           "cavolo_cappuccio_cabbage": ["nero", "verza", "rosso"], "lattuga_da_taglio_leaf_lettuce": [],
           "cicoria_da_cespo_chicory": [], "radicchio_radicchio": []}
EXTRA_KW = {"radicchio_radicchio": ["radicchio"], "lattuga_da_cespo_head_lettuce": ["lattuga", "insalata"],
            "lattuga_da_taglio_leaf_lettuce": ["lattuga", "insalata"], "uva_table_grape": ["uva da tavola"],
            "fagiolo_bean": ["fagiol"], "fagiolino_green_bean": [], "arancia_orange": ["arancia", "arance"],
            "patata_potato": ["patata", "patate"], "cipolla_estiva_summer_onion": ["cipolla", "cipolle"],
            "cipolla_invernale_winter_onion": ["cipolla", "cipolle"], "pera_pear": ["pera", "pere"],
            "susina_plum": ["susina", "susine", "prugna", "prugne"], "ciliegia_cherry": ["ciliegia", "ciliegie"],
            "nespola_loquat": ["nespol"], "fico_d_india_prickly_pear": ["fico d'india", "ficodindia"],
            "pesca_noce_nectarine": ["nettarin", "pesca noce"], "farro_emmer": ["farro"], "riso_rice": ["riso"],
            "castagna_chestnut": ["castagn", "marrone", "marroni"], "lenticchia_lentil": ["lenticchi"],
            "cece_chickpea": ["cece", "ceci"], "mela_apple": ["mela", "mele"], "pomodoro_tomato": ["pomodor"],
            "carciofo_artichoke": ["carciof"], "asparago_asparagus": ["asparag"], "limone_lemon": ["limone", "limoni"],
            "clementine_clementine": ["clementin"], "kiwi_kiwifruit": ["kiwi"], "basilico_basil": ["basilico"],
            "aglio_garlic": ["aglio"], "melanzana_eggplant": ["melanzan"], "peperone_bell_pepper": ["peperon"],
            "fragola_strawberry": ["fragol"], "melone_melon": ["melone", "meloni"], "zucca_pumpkin": ["zucca"],
            "scalogno_shallot": ["scalogn"], "cavolfiore_cauliflower": ["cavolfior"], "finocchio_fennel": ["finocch"],
            "sedano_celery": ["sedano"], "fungo_porcino_porcini_mushroom": ["fungo", "funghi"], "albicocca_apricot": ["albicocc"],
            "pesca_peach": ["pesca", "pesche"], "mandarino_mandarin": ["mandarin"], "carota_carrot": ["carot"],
            "pistacchio": [], "nocciola": [], "mais_corn": ["mais"], "cavolo_verza_savoy_cabbage": ["verza"],
            "uva": [], "fagiolo": [], "cardo_cardoon": ["cardo", "cardi"], "radicchio": []}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(dop|igp|stg|pdo|pgi)\b", " ", s)
    s = s.replace("’", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z' ]", " ", s)).strip()


def main():
    reg = [r for r in load_json(RAW / "eambrosia_it.json")["items"] if r["status"] == "Registrata" and r["qualityProductType"] == "Cibo"]
    reg16 = [r for r in reg if (r["productCategory"] or "").startswith("Classe 1.6")]
    by_norm = {norm(r["protectedName"]): r for r in reg}
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    cat = {c["id"]: c for c in load_json(CONFIG / "catalog.json")["items"]}
    stats = {"confermate": 0, "rimosse": 0, "aggiunte": 0}
    report = []
    for it in db["items"]:
        iid = it["id"]
        v = it["italian_varieties_and_territories"]
        old = list(v.get("dop_igp_labels") or [])
        kept, removed = [], []
        for lab in old:
            n = norm(lab)
            hit = by_norm.get(n) or next((r for k, r in by_norm.items() if n and (n == k or n in k or k in n) and len(k) > 6), None)
            if hit:
                kept.append(hit)
            else:
                removed.append(lab)
        kws = EXTRA_KW.get(iid) or [k.replace("-", " ") for k in cat.get(iid, {}).get("kw", [])]
        exc = EXCLUDE.get(iid, [])
        for r in reg16:
            n = norm(r["protectedName"])
            if any(re.search(r"(^|\s)" + re.escape(norm(k)), n) for k in kws if k) and not any(e in n for e in exc):
                if r not in kept:
                    kept.append(r)
                    stats["aggiunte"] += 1
                    report.append(f"+ {iid}: {r['protectedName']} {r['geographicalIndicatorTypeCode']}")
        stats["confermate"] += len(old) - len(removed)
        stats["rimosse"] += len(removed)
        for lab in removed:
            report.append(f"- {iid}: '{lab}' non trovata nel registro")
        labels = sorted({f"{r['protectedName']} {'DOP' if r['geographicalIndicatorTypeCode'] == 'PDO' else 'IGP' if r['geographicalIndicatorTypeCode'] == 'PGI' else r['geographicalIndicatorTypeCode']}" for r in kept})
        if removed:
            legacy["items"].setdefault(iid, {})["dop_igp_labels_not_in_eambrosia"] = removed
            add_discrepancy(it, "italian_varieties_and_territories.dop_igp_labels", old, labels, "eAmbrosia (registro UE)",
                            "rimosse le denominazioni non presenti nel registro")
        v["dop_igp_labels"] = labels
        v["has_dop_igp"] = bool(labels)
        v["eambrosia_verified"] = True
        mark_enriched(it, ["italian_varieties_and_territories.dop_igp_labels", "italian_varieties_and_territories.has_dop_igp",
                           "italian_varieties_and_territories.eambrosia_verified"])
        url = "https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/"
        if url not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append(url)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    save_json(RAW / "eambrosia_matching_log.json", report)
    print(stats, "| alimenti con DOP/IGP:", sum(it["italian_varieties_and_territories"]["has_dop_igp"] for it in db["items"]))
    for line in report:
        print(line)


if __name__ == "__main__":
    main()

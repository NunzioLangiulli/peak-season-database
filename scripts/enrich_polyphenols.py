"""Polyphenols from composition databases (no literature search), added to the USDA FDC carotenoids.

1. USDA Database for the Flavonoid Content of Selected Foods, Release 3.3 (2018), data/raw/usda_flavonoids/*.csv
   (exported from Flav_R03-3.accdb). Link: the product's FDC code (enrich_bioactives.FDC) -> NDB
   (sr_legacy_food.csv) -> FLAV_DAT; if missing, config/polyphenol_sources.json:usda_ndb_fallback.
   For each class (anthocyanins, flavonols, flavones, flavanones, flavan-3-ols) the sum of the measured compounds
   (mg/100 g, raw edible portion) and the 2 main compounds are reported.
2. Phenol-Explorer 3.6 (2016), data/raw/phenol_explorer/composition-data.xlsx, entry in
   config/polyphenol_sources.json:phenol_explorer:
   - total polyphenols (Folin-Ciocalteu assay), summary indicator;
   - phenolic acids, stilbenes, lignans, other polyphenols, isoflavones (chromatography, sum of the compounds);
   - flavonoid classes only if the product is not in the USDA database.
Threshold: classes >= 0.5 mg/100 g. Indicative values: variability between varieties and samples is wide.
Licences: USDA public domain; Phenol-Explorer free, commercial use with the authors' permission and citation.
Usage:  python scripts/enrich_polyphenols.py   (after enrich_bioactives.py)
"""
import csv
import io
import re
import zipfile
from collections import defaultdict

from common import DATA, RAW, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from enrich_bioactives import FDC, PRE, ZIP
from xlsx_min import read_rows

P = "nutrition_and_sustainability.bioactive_compounds"
MIN = 0.5
USDA_CLS = {"Anthocyanidins": ("Antocianine", "Anthocyanins"), "Flavonols": ("Flavonoli", "Flavonols"),
            "Flavones": ("Flavoni", "Flavones"), "Flavanones": ("Flavanoni", "Flavanones"),
            "Flavan-3-ols": ("Flavan-3-oli (catechine)", "Flavan-3-ols (catechins)")}
PE_FLAV = {"Anthocyanins": "Anthocyanidins", "Flavonols": "Flavonols", "Flavones": "Flavones",
           "Flavanones": "Flavanones", "Flavanols": "Flavan-3-ols"}
PE_OTHER = {"Phenolic acids": ("Acidi fenolici", "Phenolic acids", "acidi_fenolici"),
            "Stilbenes": ("Stilbeni", "Stilbenes", "altri_polifenoli"),
            "Lignans": ("Lignani", "Lignans", "altri_polifenoli"),
            "Isoflavonoids": ("Isoflavoni", "Isoflavones", "flavonoidi"),
            "Phenolic terpenes": ("Terpeni fenolici", "Phenolic terpenes", "altri_polifenoli"),
            "Other polyphenols": ("Altri polifenoli", "Other polyphenols", "altri_polifenoli")}
IT = {"Cyanidin": "cianidina", "Delphinidin": "delfinidina", "Malvidin": "malvidina", "Pelargonidin": "pelargonidina",
      "Peonidin": "peonidina", "Petunidin": "petunidina", "Quercetin": "quercetina", "Kaempferol": "kaempferolo",
      "Myricetin": "miricetina", "Isorhamnetin": "isoramnetina", "Apigenin": "apigenina", "Luteolin": "luteolina",
      "Hesperetin": "esperetina", "Naringenin": "naringenina", "Eriodictyol": "eriodictiolo", "(+)-Catechin": "catechina",
      "(-)-Epicatechin": "epicatechina", "(-)-Epigallocatechin": "epigallocatechina", "(+)-Gallocatechin": "gallocatechina",
      "Rosmarinic acid": "acido rosmarinico", "Carnosic acid": "acido carnosico", "Carnosol": "carnosolo", "Rosmanol": "rosmanolo",
      "5-Caffeoylquinic acid": "acido clorogenico", "Caffeic acid": "acido caffeico", "Ferulic acid": "acido ferulico",
      "p-Coumaric acid": "acido p-cumarico", "Ellagic acid": "acido ellagico", "Gallic acid": "acido gallico",
      "Punicalagin": "punicalagina", "Resveratrol": "resveratrolo", "Secoisolariciresinol": "secoisolariciresinolo",
      "Carvacrol": "carvacrolo", "Thymol": "timolo", "Eugenol": "eugenolo", "Daidzein": "daidzeina", "Genistein": "genisteina",
      "Protocatechuic acid": "acido protocatechico", "Sinapic acid": "acido sinapico", "Chlorogenic acid": "acido clorogenico",
      "3-Caffeoylquinic acid": "acido neoclorogenico", "4-Caffeoylquinic acid": "acido criptoclorogenico",
      "1,5-Dicaffeoylquinic acid": "cinarina (acido dicaffeoilchinico)", "Hydroxytyrosol": "idrossitirosolo", "Tyrosol": "tirosolo",
      "Chicoric acid": "acido cicorico", "Bergapten": "bergaptene", "Psoralen": "psoralene", "Xanthotoxin": "xantotossina",
      "Syringic acid": "acido siringico", "Gentisic acid": "acido gentisico", "4-Hydroxybenzoic acid": "acido 4-idrossibenzoico",
      "3,5-Dicaffeoylquinic acid": "acido dicaffeoilchinico", "Procyanidin dimer B1": "procianidina B1",
      "Sanguiin H-6": "sanguiina H-6 (ellagitannino)", "Lambertianin C": "lambertianina C (ellagitannino)",
      "Caffeoyl tartaric acid": "acido caftarico", "p-Coumaroyl tartaric acid": "acido coutarico",
      "Feruloyl glucose": "feruloil-glucosio", "p-Coumaroyl glucose": "p-cumaroil-glucosio",
      "3-p-Coumaroylquinic acid": "acido p-cumaroilchinico", "4-p-Coumaroylquinic acid": "acido p-cumaroilchinico",
      "(-)-Epigallocatechin 3-gallate": "epigallocatechina gallato", "Biochanin A": "biochanina A",
      "1,2-Diferuloylgentiobiose": "diferuloil-genziobiosio", "p-Coumaroyl malic acid": "acido p-cumaroilmalico",
      "Avenanthramide 2c": "avenantramide 2c", "Avenanthramide 2f": "avenantramide 2f",
      "5-Heneicosylresorcinol": "alchilresorcinoli", "5-Pentacosylresorcinol": "alchilresorcinoli", "5-Tricosylresorcinol": "alchilresorcinoli"}


def fmt(v):
    return round(v, 1) if v >= 10 else round(v, 2)


def base(n):
    """Nome dell'aglicone: 'Quercetin 3-O-glucoside' -> 'Quercetin'."""
    return re.sub(r"\s+\d[\d,']*-O-.*$|\s+(glucoside|rutinoside|galactoside|arabinoside|rhamnoside).*$", "", n.strip())


def tops(d, k=2):
    agg = defaultdict(float)
    for n, v in d.items():
        agg[base(n)] += v
    best = [n for n, v in sorted(agg.items(), key=lambda x: -x[1]) if v > 0][:k]
    return ", ".join(IT.get(n.strip(), n.strip()) for n in best), ", ".join(n.strip() for n in best)


def load_usda():
    z = zipfile.ZipFile(ZIP)
    ndb = {r["fdc_id"]: r["NDB_number"].zfill(5)
           for r in csv.DictReader(io.TextIOWrapper(z.open(PRE + "sr_legacy_food.csv"), encoding="utf-8"))}
    d = RAW / "usda_flavonoids"
    desc = {r["NDB_No"]: r["Long_Desc"] for r in csv.DictReader(open(d / "FOOD_DES.csv", encoding="utf-8-sig"))}
    nut = {r["Nutr_no"]: (r["Nutrient name"].strip(), r["Flav_Class"]) for r in csv.DictReader(open(d / "NUTR_DEF.csv", encoding="utf-8-sig"))}
    vals = defaultdict(lambda: defaultdict(dict))
    for r in csv.DictReader(open(d / "FLAV_DAT.csv", encoding="utf-8-sig")):
        name, cls = nut[r["Nutr_no"]]
        if r["Flav_Val"] not in ("", None):
            vals[r["NDB_No"]][cls][name] = float(r["Flav_Val"])
    return ndb, desc, vals


def load_pe():
    rows = read_rows(RAW / "phenol_explorer" / "composition-data.xlsx")
    h = rows[0]
    out = defaultdict(list)
    for x in rows[1:]:
        r = dict(zip(h, x))
        if r.get("units", "").startswith("mg/100 g"):
            out[r["food"]].append(r)
    return out


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "polyphenol_sources.json")
    ndb, desc, uv = load_usda()
    pe = load_pe()
    db = load_json(DATA / "database.json")
    stats = {"usda": 0, "pe": 0, "values": 0, "none": []}
    for it in db["items"]:
        n = it["nutrition_and_sustainability"]
        keep = [c for c in n.get("bioactive_compounds") or [] if c.get("source") not in ("usda_flavonoids", "phenol_explorer")]
        for c in keep:
            c.setdefault("group", "carotenoidi")
        new = []
        # --- USDA flavonoidi
        m = FDC.get(it["id"])
        code, match = None, None
        if m:
            fid = str(m[0] if isinstance(m, tuple) else m)
            if ndb.get(fid) in uv:
                code, match = ndb[fid], (m[1] if isinstance(m, tuple) else "exact")
        if not code and it["id"] in cfg["usda_ndb_fallback"]:
            code, match = cfg["usda_ndb_fallback"][it["id"]]
            code = code if code in uv else None
        if code:
            src_food = f"{desc[code]} (NDB {code})" + (" [approx]" if match == "approx" else "")
            for cls, (it_n, en_n) in USDA_CLS.items():
                comp = uv[code].get(cls, {})
                tot = sum(comp.values())
                if tot >= MIN:
                    mc, mce = tops(comp)
                    new.append({"name": it_n, "name_en": en_n, "amount": fmt(tot), "unit": "mg", "percent_nrv": None,
                                "source": "usda_flavonoids", "group": "flavonoidi", "main_compounds": mc, "main_compounds_en": mce,
                                "method": "somma dei composti misurati (aglicone)", "source_food": src_food})
            stats["usda"] += 1
            it["sources_by_topic"].setdefault("source_codes", {})["usda_flavonoids"] = {"ndb": code, "description": desc[code], "match": match}
        # --- Phenol-Explorer
        pm = cfg["phenol_explorer"].get(it["id"])
        if pm and pm[0] in pe:
            food, pmatch = pm
            rows = pe[food]
            src_food = food + (" [approx]" if pmatch == "approx" else "")
            fol = [float(r["mean"]) for r in rows if r["experimental_method_group"] == "Folin assay" and r["compound"] == "Polyphenols, total"]
            if fol:
                new.append({"name": "Polifenoli totali", "name_en": "Total polyphenols", "amount": fmt(fol[0]), "unit": "mg",
                            "percent_nrv": None, "source": "phenol_explorer", "group": "polifenoli_totali", "main_compounds": None,
                            "main_compounds_en": None, "method": "saggio di Folin-Ciocalteu", "source_food": src_food})
            groups = defaultdict(dict)
            for r in rows:
                if r["experimental_method_group"] != "Chromatography" or not r["mean"]:
                    continue
                g, sg = r["compound_group"], r["compound_sub_group"]
                if g == "Flavonoids":
                    if sg == "Isoflavonoids":
                        groups["Isoflavonoids"][r["compound"]] = float(r["mean"])
                    elif not code and sg in PE_FLAV:
                        groups["FLAV:" + PE_FLAV[sg]][r["compound"]] = float(r["mean"])
                elif g == "Other polyphenols" and sg == "Phenolic terpenes":
                    groups["Phenolic terpenes"][r["compound"]] = float(r["mean"])
                elif g in PE_OTHER:
                    groups[g][r["compound"]] = float(r["mean"])
            order = [f"FLAV:{c}" for c in USDA_CLS] + list(PE_OTHER)
            for g in order:
                comp = groups.get(g)
                if not comp or sum(comp.values()) < MIN:
                    continue
                mc, mce = tops(comp)
                if g.startswith("FLAV:"):
                    it_n, en_n = USDA_CLS[g[5:]]
                    grp = "flavonoidi"
                else:
                    it_n, en_n, grp = PE_OTHER[g]
                new.append({"name": it_n, "name_en": en_n, "amount": fmt(sum(comp.values())), "unit": "mg", "percent_nrv": None,
                            "source": "phenol_explorer", "group": grp, "main_compounds": mc, "main_compounds_en": mce,
                            "method": "somma dei composti misurati (cromatografia)", "source_food": src_food})
            stats["pe"] += 1
            it["sources_by_topic"].setdefault("source_codes", {})["phenol_explorer"] = {"food": food, "match": pmatch}
        n["bioactive_compounds"] = keep + new
        stats["values"] += len(new)
        if not n["bioactive_compounds"]:
            stats["none"].append(it["id"])
        dc = it["data_completeness"]
        dc["notes"] = " ".join(s for s in re.split(r"(?<=\.)\s+(?=[A-ZÀ-Ý])", dc["notes"]) if not s.startswith("Polifenoli:")).strip()
        if new:
            dc["notes"] += (" Polifenoli: " + ", ".join(sorted({c["source"] for c in new})).replace("usda_flavonoids", "USDA Flavonoid Database 3.3")
                            .replace("phenol_explorer", "Phenol-Explorer 3.6") + " (valori indicativi per 100 g di prodotto crudo).")
            mark_enriched(it, [P])
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(f"products with USDA flavonoids: {stats['usda']}, with Phenol-Explorer: {stats['pe']}, values added: {stats['values']}")
    print("still without bioactive compounds:", stats["none"])


if __name__ == "__main__":
    main()

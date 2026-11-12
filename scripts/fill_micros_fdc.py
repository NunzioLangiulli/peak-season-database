"""Vitamine/minerali da USDA FDC SR Legacy quando CREA e BDA-IEO non li riportano (lista vuota).

Esempi: CREA 005210 'Cavolo verza, cruda' e 007330 'Peschenoci, fresche' hanno solo macronutrienti; CREA 006010
'pleurotes' non ha vitamine. Codice FDC da enrich_bioactives.FDC. Fonte dichiarata in ogni voce (source: usda_fdc).
Uso:  python scripts/fill_micros_fdc.py   (dopo enrich_nutrition / enrich_fdc)
"""
import csv
import io
import zipfile

from common import DATA, finalize_completeness, load_json, mark_enriched, save_json
from enrich_bioactives import FDC, PRE, ZIP
from enrich_nutrition import NAMES, NRV

NBR = {"320": "vit_a", "323": "vit_e", "430": "vit_k", "401": "vit_c", "404": "vit_b1", "405": "vit_b2", "406": "niacin",
       "415": "vit_b6", "417": "folate", "418": "vit_b12", "306": "potassium", "301": "calcium", "305": "phosphorus",
       "304": "magnesium", "303": "iron", "309": "zinc", "312": "copper", "315": "manganese", "317": "selenium", "307": "sodium"}


def main():
    db = load_json(DATA / "database.json")
    todo = {it["id"]: it for it in db["items"]
            if FDC.get(it["id"]) and (not it["nutrition_and_sustainability"]["vitamins"] or not it["nutrition_and_sustainability"]["minerals"])}
    fids = {str(v[0] if isinstance(v, tuple) else v): k for k, v in FDC.items() if k in todo}
    z = zipfile.ZipFile(ZIP)
    rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(PRE + n), encoding="utf-8"))  # noqa: E731
    nid = {n["id"]: n["nutrient_nbr"] for n in rd("nutrient.csv") if n["nutrient_nbr"] in NBR}
    desc = {f["fdc_id"]: f["description"] for f in rd("food.csv") if f["fdc_id"] in fids}
    vals = {}
    for r in rd("food_nutrient.csv"):
        if r["fdc_id"] in fids and r["nutrient_id"] in nid:
            vals.setdefault(fids[r["fdc_id"]], {})[NBR[nid[r["nutrient_id"]]]] = float(r["amount"])
    for iid, it in todo.items():
        n = it["nutrition_and_sustainability"]
        v = vals.get(iid, {})
        fid = [f for f, k in fids.items() if k == iid][0]
        for lst, typ, field in ((n["vitamins"], "v", "vitamins"), (n["minerals"], "m", "minerals")):
            if lst:
                continue
            for k, (it_n, en_n, *_r, t) in NAMES.items():
                if t != typ or not v.get(k):
                    continue
                ref = NRV.get(k)
                lst.append({"name": it_n, "name_en": en_n, "amount": v[k], "unit": NRV.get(k, (0, "mg"))[1],
                            "percent_nrv": round(v[k] / ref[0] * 100, 1) if ref else None, "source": "usda_fdc"})
            mark_enriched(it, [f"nutrition_and_sustainability.{field}"])
        url = f"https://fdc.nal.usda.gov/food-details/{fid}/nutrients"
        if url not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append(url)
        it["data_completeness"]["notes"] += (f" Vitamine/minerali assenti in CREA/BDA-IEO: integrati da USDA FDC {fid} "
                                             f"'{desc.get(fid)}' (fonte non italiana).")
        finalize_completeness(it)
        print(iid, len(n["vitamins"]), "vitamine,", len(n["minerals"]), "minerali")
    save_json(DATA / "database.json", db)


if __name__ == "__main__":
    main()

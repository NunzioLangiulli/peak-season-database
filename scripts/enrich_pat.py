"""Traditional Agri-food Products (PAT) linked to each product.

Source: MASAF, 26th revision of the national PAT list (2026), 'Tabella con suddivisione per Regione e categoria
merceologica' (data/raw/pat/pat_xxvi_2026_tabella.xlsx; page https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151).
The category 'Prodotti vegetali allo stato naturale o trasformati' is used. Linked by keyword (stem of the Italian
name, whole word) with exclusions for false positives: config/pat_keywords.json.
nutrition_and_sustainability.traditional_products_pat = {count, regions[], products[{name, region}], source, revision}
Usage:  python scripts/enrich_pat.py
"""
import re
import zipfile

from common import DATA, RAW, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from xlsx_min import read_rows

F = RAW / "pat" / "pat_xxvi_2026_tabella.xlsx"
URL = "https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/24151"
CAT = "prodotti vegetali"
N = "nutrition_and_sustainability"


def load():
    z = zipfile.ZipFile(F)
    wb = z.read("xl/workbook.xml").decode()
    rels = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', z.read("xl/_rels/workbook.xml.rels").decode()))
    out = []
    for name, rid in re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb):
        region = name.strip().title().replace("D'Aosta", "d'Aosta").replace("Prov.Trento", "Prov. Trento")
        cat = ""
        for x in read_rows(F, "xl/" + rels[rid].lstrip("/").replace("xl/", "")):
            x = (x + ["", "", ""])[:3]
            if x[0].strip():
                cat = x[0].strip()
            if CAT in cat.lower() and x[2].strip() and x[2].strip() != "Prodotto":
                out.append({"name": re.sub(r"\s+", " ", x[2]).strip(), "region": region})
    return out


def main():
    pats = load()
    kw = load_json(ROOT / "scripts" / "config" / "pat_keywords.json")
    db = load_json(DATA / "database.json")
    tot = 0
    for it in db["items"]:
        k = kw["items"].get(it["id"])
        if not k:
            it[N]["traditional_products_pat"] = {"count": 0, "regions": [], "products": [], "source": URL, "revision": "XXVI (2026)"}
            finalize_completeness(it)
            continue
        inc = re.compile(r"\b(" + "|".join(k["include"]) + r")", re.I)
        exc = re.compile(r"\b(" + "|".join(k.get("exclude", [])) + r")", re.I) if k.get("exclude") else None
        found = [p for p in pats if inc.search(p["name"]) and not (exc and exc.search(p["name"]))]
        seen, prods = set(), []
        for p in found:
            if (p["name"], p["region"]) not in seen:
                seen.add((p["name"], p["region"]))
                prods.append(p)
        it[N]["traditional_products_pat"] = {"count": len(prods), "regions": sorted({p["region"] for p in prods}),
                                             "products": prods, "source": URL, "revision": "XXVI (2026)"}
        mark_enriched(it, [f"{N}.traditional_products_pat"])
        if URL not in it["sources_by_topic"]["other_urls"]:
            it["sources_by_topic"]["other_urls"].append(URL)
        tot += len(prods)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(f"plant PATs in the list: {len(pats)}; links: {tot}")
    top = sorted(db["items"], key=lambda i: -i[N]["traditional_products_pat"]["count"])[:12]
    print([(i["id"], i[N]["traditional_products_pat"]["count"]) for i in top])


if __name__ == "__main__":
    main()

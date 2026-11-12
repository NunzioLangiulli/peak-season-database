"""Report of products left out of the database by the inclusion rule (data/excluded_candidates_report.md).

Rule: at least 2 seasonality or storage sources + a CREA or BDA-IEO composition record.
Candidates are in scripts/config/excluded_candidates_review.json (collected from the calendars and from eAmbrosia).
For each one the report searches the name (IT/EN regex) in the raw data already downloaded and counts the sources; relevance and
proposal are a declared judgement, to be confirmed by the project owner.
Usage:  python scripts/make_excluded_report.py
"""
import re
from datetime import date

from common import CONFIG, DATA, RAW, load_json


STATUS_EN = {"incluso il 2026-11-05": "included on 2026-11-05", "escluso su decisione dell'utente (2026-11-05)": "excluded by owner decision (2026-11-05)"}
REL_EN = {"alta": "high", "media": "medium", "bassa": "low"}


def names(o):
    if isinstance(o, dict):
        return [k for k in o if not k.startswith("_")]
    return list(o)


def main():
    cfg = load_json(CONFIG / "excluded_candidates_review.json")["candidates"]
    lp = load_json(RAW / "local_pdf_lists.json")
    src = {
        "WWF": names(load_json(RAW / "wwf_calendar.json")["rows"]),
        "Greenpeace": [k.split(":", 1)[-1] for k in names(load_json(RAW / "greenpeace_months.json"))],
        "Altroconsumo": names(load_json(RAW / "altroconsumo_items.json")),
        "Orto da Coltivare (tabelle)": lp["odc_rows"]["rows"],
        "Orto da Coltivare (sito)": [u.rstrip("/").rsplit("/", 1)[-1].replace("-", " ") for u in load_json(RAW / "sitemap_odc.json")],
        "Bio Suisse": lp["biosuisse"]["rows"] if isinstance(lp["biosuisse"], dict) else lp["biosuisse"],
    }
    cons = {
        "UC Davis": list(load_json(RAW / "ucdavis_slugs.json")["slugs"].values()),
        "FoodKeeper": names(load_json(RAW / "foodkeeper_produce.json")),
        "USDA HB66": names(load_json(RAW / "usda_hb66_table1.json")),
    }
    crea = names(load_json(RAW / "crea_list.json"))
    bda = names(load_json(RAW / "bda_codes.json"))
    eu = load_json(RAW / "eufic_fvlist.json")
    gi = [x["protectedName"] for x in load_json(RAW / "eambrosia_it.json")["items"]
          if (x.get("productCategory") or "").startswith(("Classe 1.6", "Classe 1.8")) and x["status"] == "Registrata"]
    rows, add = [], []
    for c in cfg:
        r = re.compile(c["re"], re.I)
        it_s = [k for k, v in src.items() if k != "Bio Suisse" and any(r.search(x) for x in v)]
        bs = any(r.search(x) for x in src["Bio Suisse"])
        euc = sorted({cty.strip() for g in ("Fruit", "Vegetable") for k in c["eufic"] if k in eu[g] for _, cty in eu[g][k]})
        co = [k for k, v in cons.items() if any(r.search(x) for x in v)]
        rc = re.compile(c.get("comp_re", c["re"]).replace("\\b", ""), re.I)  # at the start of the entry: excludes composite products
        cr = [x for x in crea if rc.match(x)][:2]
        bd = [x for x in bda if rc.match(x)][:2]
        g = [x for x in gi if r.search(x)]
        seasonal = it_s + (["Bio Suisse"] if bs else []) + (["EUFIC"] if euc else [])
        n_src = len(seasonal) + len(co)
        comp = bool(cr or bd)
        why = []
        if n_src < 2:
            why.append(f"{n_src} seasonality/storage source")
        if not comp:
            why.append("no CREA/BDA record")
        if not why:
            why.append("requirements met: was not in the initial candidate list")
        rows.append([f'{c["en"]} ({c["it"]})', STATUS_EN.get(c.get("status"), "to decide"), ", ".join(it_s) or "–", ("Bio Suisse" if bs else "") + (("; " if bs and euc else "") + f"EUFIC {len(euc)} countries" if euc else "") or "–",
                     ", ".join(co) or "–", "; ".join(cr) or "–", "; ".join(bd) or "–", "; ".join(g) or "–",
                     "; ".join(why), f"{REL_EN[c['rel'][0]]} – {c['rel_en']}", c["prop_en"]])
        if not [w for w in why if not w.startswith("requirements")] or c["rel"][0] == "alta":
            add.append(c["en"])
    L = ["# Products not included in the database\n",
         f"Generated on {date.today().isoformat()} by `scripts/make_excluded_report.py`.\n",
         "**Inclusion rule** for new products: at least 2 seasonality or storage sources and a CREA or BDA-IEO composition record. "
         "It ensures every record has sourced seasonality and nutrition values. White truffle was added as an exception "
         "(empty nutrition, seasonality set by law).\n",
         "**How candidates were collected**: every entry of the calendars used (WWF, Greenpeace, Altroconsumo, Orto da Coltivare, Bio Suisse, "
         "EUFIC for 29 countries) that does not match a product in the database, plus Italian PDO/PGI fruit and vegetable products from the "
         "eAmbrosia register with no matching product, plus some typical Italian products missing from every calendar (e.g. agretti, lampascioni, "
         "cicerchia). The source columns are computed by searching the name in the raw data already downloaded; relevance and proposal are a "
         "declared judgement, to be confirmed.\n",
         "**Limitation**: a product missing from all these lists (e.g. many local varieties) was not considered; for those, "
         "the MASAF PAT list, already linked to the products, is a starting point.\n",
         "**Owner decision (5 November 2026)**: all candidates included except bergamot, caper, sorrel, strawberry tree and purslane, even with incomplete fields (Status column). For included products the columns show the sources available at the time of inclusion.\n",
         "## Candidates\n",
         "| Candidate | Status | Italian calendars | Other calendars | Storage | CREA | BDA-IEO | PDO/PGI | Why it is out | Relevance | Proposal |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {"high": 0, "medium": 1, "low": 2}
    for r in sorted(rows, key=lambda r: (order[r[9].split(" ")[0]], r[0])):
        L.append("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |")
    L += ["\n## To evaluate first\n",
          "Candidates with high relevance or that already meet the rule: " + ", ".join(add) + ".\n",
          "Notes:\n",
          "- **Nuts** (walnut, hazelnut, almond, pistachio): they have CREA/BDA records and PDO/PGI, but the seasonal calendars do not list them. "
          "Including them is a scope choice for the app (today: fresh fruit and vegetables).",
          "- **Varieties or forms of products already present** (puntarelle, snow peas, mirabelles, wild asparagus): better added as varieties, "
          "as for the flat peach, without creating new records.",
          "- **Romanesco broccoli**: no specific CREA/BDA record; cauliflower or broccoli could be used as a declared approximation.",
          "- **Wild mushrooms** (chanterelle, morel, cardoncello): regional mushroom laws rarely give periods per species; institutional "
          "mycological sheets would be needed, as for Caesar's mushroom.\n"]
    (DATA / "excluded_candidates_report.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote data/excluded_candidates_report.md:", len(rows), "candidates")


if __name__ == "__main__":
    main()

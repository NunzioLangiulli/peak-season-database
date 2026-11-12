"""Report degli alimenti rimasti fuori dal database per la regola di ammissione (data/excluded_candidates_report.md).

Regola: almeno 2 fonti stagionali o di conservazione + una scheda di composizione CREA o BDA-IEO.
I candidati sono in scripts/config/excluded_candidates_review.json (raccolti dai calendari e da eAmbrosia).
Per ognuno il report cerca il nome (regex IT/EN) nei dati grezzi già scaricati e conta le fonti; rilevanza e
proposta sono un giudizio dichiarato, da confermare con l'utente.
Uso:  python scripts/make_excluded_report.py
"""
import re
from datetime import date

from common import CONFIG, DATA, RAW, load_json


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
        rc = re.compile(c.get("comp_re", c["re"]).replace("\\b", ""), re.I)  # a inizio voce: esclude i prodotti composti
        cr = [x for x in crea if rc.match(x)][:2]
        bd = [x for x in bda if rc.match(x)][:2]
        g = [x for x in gi if r.search(x)]
        seasonal = it_s + (["Bio Suisse"] if bs else []) + (["EUFIC"] if euc else [])
        n_src = len(seasonal) + len(co)
        comp = bool(cr or bd)
        why = []
        if n_src < 2:
            why.append(f"{n_src} fonte stagionale/conservazione")
        if not comp:
            why.append("nessuna scheda CREA/BDA")
        if not why:
            why.append("requisiti soddisfatti: non era nella lista iniziale dei candidati")
        rows.append([c["it"], c.get("status", "da decidere"), ", ".join(it_s) or "–", ("Bio Suisse" if bs else "") + (("; " if bs and euc else "") + f"EUFIC {len(euc)} Paesi" if euc else "") or "–",
                     ", ".join(co) or "–", "; ".join(cr) or "–", "; ".join(bd) or "–", "; ".join(g) or "–",
                     "; ".join(why), f"{c['rel'][0]} – {c['rel'][1]}", c["prop"]])
        if not [w for w in why if not w.startswith("requisiti")] or c["rel"][0] == "alta":
            add.append(c["it"])
    L = ["# Alimenti non inclusi nel database\n",
         f"Generato il {date.today().isoformat()} da `scripts/make_excluded_report.py`.\n",
         "**Regola di ammissione** usata per i nuovi alimenti: almeno 2 fonti stagionali o di conservazione e una scheda di composizione "
         "CREA o BDA-IEO. Serve a garantire che ogni scheda abbia stagionalità e valori nutrizionali da fonte. Il tartufo bianco è stato "
         "aggiunto in deroga (nutrizione vuota, stagionalità per legge).\n",
         "**Come sono stati raccolti i candidati**: tutte le voci dei calendari usati (WWF, Greenpeace, Altroconsumo, Orto da Coltivare, Bio Suisse, "
         "EUFIC per 29 Paesi) che non corrispondono a un alimento del database, più i prodotti ortofrutticoli italiani DOP/IGP del registro "
         "eAmbrosia senza alimento corrispondente, più alcuni prodotti tipici italiani assenti da tutti i calendari (es. agretti, lampascioni, "
         "cicerchia). Le colonne sulle fonti sono calcolate cercando il nome nei dati grezzi già scaricati; rilevanza e proposta sono un mio "
         "giudizio, da confermare.\n",
         "**Limite**: un prodotto che non compare in nessuna di queste liste (es. molte varietà locali) non è stato considerato; per quelli "
         "si può partire dall'elenco PAT del MASAF, già collegato agli alimenti.\n",
         "**Decisione dell'utente (5 novembre 2026)**: inclusi tutti i candidati tranne bergamotto, cappero, acetosa, corbezzolo e portulaca, anche con campi incompleti (colonna Stato). Per quelli inclusi le colonne mostrano le fonti disponibili al momento dell'inclusione.\n",
         "## Candidati\n",
         "| Candidato | Stato | Calendari italiani | Altri calendari | Conservazione | CREA | BDA-IEO | DOP/IGP | Perché è fuori | Rilevanza | Proposta |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {"alta": 0, "media": 1, "bassa": 2}
    for r in sorted(rows, key=lambda r: (order[r[9].split(" ")[0]], r[0])):
        L.append("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |")
    L += ["\n## Da valutare per primi\n",
          "Candidati con rilevanza alta o che soddisfano già la regola: " + ", ".join(add) + ".\n",
          "Note:\n",
          "- **Frutta secca** (noce, nocciola, mandorla, pistacchio): hanno schede CREA/BDA e DOP/IGP, ma i calendari stagionali non li riportano. "
          "Includerli è una scelta di perimetro dell'app (oggi: frutta e verdura fresca).",
          "- **Varietà o forme di alimenti già presenti** (puntarelle, taccole, mirabelle, asparago selvatico): conviene aggiungerle come varietà, "
          "come per la pesca tabacchiera, senza creare nuove schede.",
          "- **Broccolo romanesco**: nessuna scheda CREA/BDA specifica; si potrebbe usare cavolfiore o broccolo come approssimazione dichiarata.",
          "- **Funghi spontanei** (finferlo, spugnola, cardoncello): le leggi regionali sui funghi raramente danno periodi per specie; servirebbero "
          "schede micologiche istituzionali come per l'ovolo.\n"]
    (DATA / "excluded_candidates_report.md").write_text("\n".join(L), encoding="utf-8")
    print("scritto data/excluded_candidates_report.md:", len(rows), "candidati")


if __name__ == "__main__":
    main()

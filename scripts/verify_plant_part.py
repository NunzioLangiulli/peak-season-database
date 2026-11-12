"""Verifica botany.plant_part_used della bozza sui testi delle fonti.

Si cercano le parole che descrivono la parte consumata nella sezione 'Scientific Name and Introduction' del capitolo
USDA HB66 e nelle pagine Orto da Coltivare / My-PersonalTrainer / Altroconsumo dell'alimento. Il valore è verificato
se almeno una fonte usa un termine coerente; altrimenti resta da verificare.
Uso:  python scripts/verify_plant_part.py [--dry-run]
"""
import argparse
import re

from common import DATA, finalize_completeness, load_json, mark_enriched, save_json
from enrich_postharvest import MAP, load_hb66
from text_corpus import corpus, norm

KW = {
    "frutto": r"\b(fruits?|berry|berries|frutt[oi]|bacca|bacche|drupa|pepo|esperidio|pomo)\b",
    "foglia": r"\b(leaf|leaves|leafy|foglia|foglie|cespo|rosetta)\b",
    "radice": r"\b(root|taproot|radice|fittone)\b",
    "tubero": r"\b(tubers?|tuber[oi])\b",
    "bulbo": r"\b(bulbs?|bulb[oi]|spicchi|cloves)\b",
    "infiorescenza_bocciolo": r"\b(inflorescences?|flower buds?|immature flower|infiorescenz\w*|bocciol\w*|capolin\w*|corymb|curd|sprouts?|buds?)\b",
    "fusto_costa": r"\b(stems?|stalks?|petioles?|spears?|shoots?|enlarged stem|fust[oi]|cost[ae]|turion\w*|grumol\w*|guaina|pseudostem|leaf bases?)\b",
    "seme": r"\b(seeds?|grains?|kernels?|legumes?|nuts?|sem[ei]|chicc\w*|granell\w*|cariossid\w*|baccell\w*)\b",
    "fungo_carpoforo": r"\b(fruiting bod\w*|mushrooms?|carpofor\w*|cappello|gambo|sporocarp\w*|ascocarp\w*)\b",
}


def intro(txt):
    m = re.search(r"Scientific Name and Introduction(.*?)(Quality Characteristics|Horticultural Maturity|Grades)", txt, re.S)
    return m.group(1) if m else txt[:2500]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    db = load_json(DATA / "database.json")
    chap, _ = load_hb66()
    ok = 0
    for it in db["items"]:
        part = it["botany"]["plant_part_used"]
        if "botany.plant_part_used" not in it["data_completeness"].get("fields_pending_verification", []) or not part:
            continue
        m = MAP.get(it["id"])
        docs = []
        if m and m[0] in chap:
            docs.append(("usda_hb66", intro(chap[m[0]]["text"])))
        docs += [(k, t) for k, _u, t in corpus(it)]
        name_words = [w for w in norm(it["names"]["it"]).split() if len(w) > 3][:1]
        hits = []
        for k, t in docs:
            n = norm(t)
            # il termine deve comparire vicino al nome dell'alimento (entro 150 caratteri) per evitare citazioni generiche
            for mm in re.finditer(KW[part], n):
                win = n[max(0, mm.start() - 150):mm.end() + 150]
                if k == "usda_hb66" or any(w[:5] in win for w in name_words):
                    hits.append(k)
                    break
        hits = sorted(set(hits))
        if a.dry_run:
            print(("OK " if hits else "-- ") + it["id"][:28].ljust(28), part.ljust(22), hits)
            continue
        if hits:
            mark_enriched(it, ["botany.plant_part_used"])
            it["data_completeness"]["notes"] += f" Parte usata '{part}' confermata dai testi di: {', '.join(hits)}."
            ok += 1
        finalize_completeness(it)
    if not a.dry_run:
        save_json(DATA / "database.json", db)
        print("parti confermate:", ok)


if __name__ == "__main__":
    main()

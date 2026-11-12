"""Terminologia dei testi per l'utente (revisione UX writing, 2026-11-12). Idempotente.

"Alimento/alimenti" e "food/foods" suonano freddi per un'app di frutta e verdura: nei testi per l'utente si usa
"prodotto/prodotti" (IT) e "product"/"produce" (EN: "produce" per il plurale e il collettivo). Restano invariati:
i nomi propri (CREA "Alimenti e Nutrizione", "Banca Dati di Composizione degli Alimenti", "Slow Food", "Agri-food"),
le espressioni sull'alimentazione in generale ("alimenti di origine animale" / "animal-based foods") e le note
interne in data_completeness. Le parole con iniziale maiuscola (nomi propri ed etichette) non vengono toccate.
Uso:  python scripts/ux_terminology.py   (penultimo passo, prima di title_case_labels.py)
"""
import re

from common import DATA, load_json, save_json

KEEP = re.compile(r"origine animale|animal-based foods|Agri-food|Slow Food|Food Composition")
IT = [  # (regex, sostituzione) in ordine: prima le forme con articolo
    (r"\bquesto alimento\b", "questo prodotto"), (r"\bdell'alimento\b", "del prodotto"), (r"\ball'alimento\b", "al prodotto"),
    (r"\bl'alimento\b", "il prodotto"), (r"\bun alimento\b", "un prodotto"), (r"\bdegli alimenti\b", "dei prodotti"),
    (r"\bagli alimenti\b", "ai prodotti"), (r"\bdagli alimenti\b", "dai prodotti"), (r"\bnegli alimenti\b", "nei prodotti"),
    (r"\bsugli alimenti\b", "sui prodotti"), (r"\bgli alimenti\b", "i prodotti"), (r"\balimento\b", "prodotto"), (r"\balimenti\b", "prodotti"),
]
EN = [
    (r"\bhow food is produced\b", "how produce is grown"), (r"\bthis very food\b", "this very product"), (r"\bthis food\b", "this product"),
    (r"\ba food\b", "a product"), (r"\bthe same food\b", "the same product"), (r"\bevery food\b", "every product"),
    (r"(?<![-\w])foods\b", "produce"), (r"(?<![-\w])food\b", "product"),
]


def fix(s, rules):
    if not isinstance(s, str) or KEEP.search(s):
        if isinstance(s, str) and KEEP.search(s):          # proteggi solo le parti da conservare
            parts = re.split(f"({KEEP.pattern})", s)
            return "".join(p if KEEP.fullmatch(p) else fix(p, rules) for p in parts)
        return s
    for rx, rep in rules:
        s = re.sub(rx, rep, s)                               # solo minuscole: i nomi propri restano
    return s


def walk(o, stats):
    if isinstance(o, dict):
        if isinstance(o.get("it"), str) and isinstance(o.get("en"), str):
            new_it, new_en = fix(o["it"], IT), fix(o["en"], EN)
            if (new_it, new_en) != (o["it"], o["en"]):
                stats[0] += 1
            o["it"], o["en"] = new_it, new_en
        for k, v in o.items():
            if k not in ("data_completeness", "name", "it", "en"):
                walk(v, stats)
    elif isinstance(o, list):
        for v in o:
            walk(v, stats)


def main():
    db = load_json(DATA / "database.json")
    stats = [0]
    walk(db, stats)
    save_json(DATA / "database.json", db)
    print("testi aggiornati (alimento/food -> prodotto/produce):", stats[0])


if __name__ == "__main__":
    main()

"""IT/EN summary of the EUFIC article "Are seasonal fruit and vegetables better for the environment?" (09/09/2020)
in metadata.sustainable_diet_summary. Text reworked (not copied) from the article's points, raw text in
data/raw/eufic_article.txt. The draft summary (which cited an "up to 50%" not present in the article) goes to
draft_legacy_values.json.
Usage:  python scripts/set_sustainability_summary.py
"""
from common import DATA, load_json, save_json

SUMMARY = {
    "it": ("Secondo EUFIC, frutta e verdura hanno in genere un impatto climatico molto inferiore agli alimenti di origine "
           "animale (le emissioni di gas serra sono 10-50 volte più basse di carne bovina e latticini). Il vantaggio della "
           "stagionalità non dipende tanto dai chilometri percorsi quanto dal modo di produzione: i prodotti con l'impronta "
           "più bassa sono quelli coltivati all'aperto nella loro stagione naturale e consumati nella stessa regione, perché "
           "non richiedono energia per serre riscaldate, illuminazione o lunghe conservazioni in cella frigorifera."),
    "en": ("According to EUFIC, fruit and vegetables generally have a much lower climate impact than animal-based foods "
           "(greenhouse gas emissions 10-50 times lower than beef and dairy). The benefit of eating seasonally depends less on "
           "transport distance than on how food is produced: the lowest footprint comes from produce grown outdoors in its "
           "natural season and eaten in the same region, since it needs no energy for heated greenhouses, lighting or long "
           "cold storage."),
}
KEY_POINTS = {
    "it": [
        "Il sistema alimentare mondiale genera circa il 26% delle emissioni globali di gas serra.",
        "Frutta e verdura emettono 10-50 volte meno gas serra di carne bovina e latticini.",
        "Il trasporto pesa di solito meno della produzione, tranne per i prodotti spediti in aereo (es. frutti di bosco, frutta tropicale, fagiolini).",
        "Un pomodoro locale fuori stagione coltivato in serra riscaldata può avere un'impronta più alta di uno di stagione coltivato all'aperto in Spagna e trasportato.",
        "Mele conservate molti mesi in cella frigorifera possono avere un'impronta più alta di mele di stagione importate dall'altro emisfero.",
        "\"Stagionale\" può essere locale (prodotto e consumato nella stessa zona) o globale (prodotto in stagione altrove).",
        "Le emissioni di gas serra sono solo uno degli impatti: contano anche acqua, inquinamento da fertilizzanti e uso del suolo.",
    ],
    "en": [
        "The global food system accounts for about 26% of global greenhouse gas emissions.",
        "Fruit and vegetables emit 10-50 times less greenhouse gas than beef and dairy.",
        "Transport usually matters less than production, except for air-freighted produce (e.g. berries, tropical fruit, green beans).",
        "An out-of-season local tomato grown in a heated greenhouse can have a higher footprint than an in-season tomato grown outdoors in Spain and shipped.",
        "Apples cold-stored for many months can have a higher footprint than in-season apples imported from the other hemisphere.",
        "\"Seasonal\" can be local (produced and eaten in the same area) or global (produced in season elsewhere).",
        "Greenhouse gas emissions are only one impact: water, fertiliser pollution and land use matter too.",
    ],
}


def main():
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    s = db["metadata"]["sustainable_diet_summary"]
    if s.get("status") == "from_user_draft_unverified":
        legacy.setdefault("metadata", {})["sustainable_diet_summary"] = {"it": s["it"], "en": s["en"]}
    db["metadata"]["sustainable_diet_summary"] = {**SUMMARY, "key_points": KEY_POINTS, "status": "verified_from_source",
                                                  "source_url": "https://www.eufic.org/en/healthy-living/article/are-seasonal-fruit-and-vegetables-better-for-the-environment",
                                                  "source_date": "2020-09-09"}
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print("EUFIC summary updated")


if __name__ == "__main__":
    main()

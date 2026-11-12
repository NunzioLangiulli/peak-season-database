"""Revisione della sezione "Dove Conservarlo" (2026-11-13, richiesta dell'utente). Idempotente.
Applica al database le regole ora scritte in apply_home_storage.py senza rigenerare tutto home_storage:
- etichetta room_temperature: "A Temperatura Ambiente" / "At Room Temperature" (uniforme alle altre);
- consiglio (tip): niente "Una volta tagliato va sempre in frigorifero" per il frigorifero e per i prodotti senza luogo;
  niente frasi che ripetono storage_instructions (mostrato subito sopra nell'app). Tip vuoto = null.
Uso:  python scripts/apply_storage_display_review.py   (dopo apply_home_storage.py; poi ux_terminology e title_case_labels)
"""
from apply_home_storage import LABEL, TIPS, home_tip
from enrich_chilling import set_na
from common import CONFIG, DATA, finalize_completeness, load_json, save_json


def main():
    cfg = load_json(CONFIG / "ucdavis_home_storage.json")["items"]
    db = load_json(DATA / "database.json")
    n = {"label": 0, "tip": 0, "tip_removed": 0}
    for it in db["items"]:
        hs = it["ripening_and_storage"].get("home_storage")
        if not hs:
            continue
        loc = hs.get("location")
        if loc:
            lab = {"it": LABEL[loc][0], "en": LABEL[loc][1]}
            if (hs.get("label") or {}).get("it", "").lower() != lab["it"].lower():
                hs["label"] = lab
                n["label"] += 1
        u = cfg.get(it["id"])
        new = home_tip(it["id"], loc, TIPS.get(it["id"]) or (TIPS[u[2]] if u and len(u) > 2 else None))
        if new != hs.get("tip"):
            n["tip"] += 1
            n["tip_removed"] += new is None
            hs["tip"] = new
            if new is None:                                   # campo vuoto per scelta, non dato mancante
                set_na(it, ["ripening_and_storage.home_storage.tip"])
        finalize_completeness(it)
    m = db["metadata"].get("home_storage_legend") or {}
    if m.get("locations"):
        m["locations"]["room_temperature"] = {"it": LABEL["room_temperature"][0], "en": LABEL["room_temperature"][1]}
    save_json(DATA / "database.json", db)
    print(n)


if __name__ == "__main__":
    main()

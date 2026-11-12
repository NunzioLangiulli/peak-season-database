"""Correzioni emerse dal ricontrollo sistematico (audit_db.py), riproducibili.

1. refrigerated_days uguale alla durata PROFESSIONALE (commercial_optimal_days, USDA HB66) per alimenti senza dato
   domestico FoodKeeper: non e' una durata da frigo di casa -> null (mancante), valore spostato in legacy/nota.
2. Soglia di danno da freddo presente per prodotti NON sensibili (valore della bozza) -> null, non pertinente.
3. Cavolo nero: zuccheri > carboidrati disponibili per costruzione del dato FDC (carboidrati per differenza - fibra):
   annotato, valori della fonte lasciati invariati.
Uso:  python scripts/fix_audit.py   (dopo mark_structural_na.py)
"""
from common import DATA, finalize_completeness, load_json, save_json
from enrich_chilling import set_na

P = "ripening_and_storage.postharvest_physiology"


def main():
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    log = []
    for it in db["items"]:
        ph = it["ripening_and_storage"]["postharvest_physiology"]
        sl, ci = ph["estimated_shelf_life_days"], ph["chilling_injury"]
        dc = it["data_completeness"]
        lg = legacy["items"].setdefault(it["id"], {})
        fk = "FoodKeeper" in (sl.get("basis") or "") and "Durate domestiche" in (sl.get("basis") or "")
        if sl.get("refrigerated_days") and sl["refrigerated_days"] == sl.get("commercial_optimal_days") and not fk:
            lg[f"{P}.estimated_shelf_life_days.refrigerated_days"] = sl["refrigerated_days"]
            dc["notes"] += (f" Durata in frigorifero di casa non disponibile: il valore {sl['refrigerated_days']} giorni era la durata "
                            "in condizioni professionali (USDA HB66), che resta in commercial_optimal_days.")
            sl["refrigerated_days"] = None
            dc["fields_pending_verification"] = [p for p in dc.get("fields_pending_verification", []) if not p.endswith("refrigerated_days")]
            log.append((it["id"], "refrigerated_days"))
        if ci.get("susceptible") is False and ci.get("critical_temperature_c") is not None:
            lg[f"{P}.chilling_injury.critical_temperature_c"] = ci["critical_temperature_c"]
            ci["critical_temperature_c"] = None
            set_na(it, [f"{P}.chilling_injury.critical_temperature_c"])
            log.append((it["id"], "critical_temperature_c"))
        if it["id"] == "cavolo_nero_black_kale" and "zuccheri superiori" not in dc["notes"]:
            dc["notes"] += (" Nella fonte (USDA FDC 168421) gli zuccheri (0,99 g) risultano superiori ai carboidrati disponibili (0,3 g), "
                            "calcolati come carboidrati per differenza meno fibra: incoerenza interna della fonte, valori lasciati come pubblicati.")
            log.append((it["id"], "note sugars"))
        pr = it["nutrition_and_sustainability"].get("protein_reference")
        if pr and pr.get("claim_note") is None:
            set_na(it, ["nutrition_and_sustainability.protein_reference.claim_note"])
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(log)


if __name__ == "__main__":
    main()

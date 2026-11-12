"""Riferimento proteico per l'Italia (nutrition_and_sustainability.protein_reference).

Riferimento scientifico nazionale: LARN - SINU, IV revisione 2014 (fonti_locali/Tabelle-riassuntive_SINU.pdf):
  adulti 18-64 anni PRI 0,90 g/kg/die -> 63 g/die uomo (70 kg), 54 g/die donna (60 kg)
  65 anni e oltre   PRI 1,1 g/kg/die  -> 77 g/die uomo, 66 g/die donna
Riferimento di etichettatura UE: RI proteine 50 g/die (Reg. UE 1169/2011, Allegato XIII, parte B).
Claim (Reg. CE 1924/2006): "fonte di/ad alto contenuto di proteine" = >=12% / >=20% dell'energia da proteine.
Il criterio è legale ma relativo: in ortaggi molto poco calorici scatta anche con pochi grammi. Se la porzione
di 100 g copre meno del 10% della PRI LARN (donna adulta, 5,4 g), il claim resta (è conforme) ma viene
affiancato da una nota che lo contestualizza.
Uso:  python scripts/enrich_protein.py
"""
from common import DATA, finalize_completeness, load_json, mark_enriched, save_json

PRI = {"m": 63, "f": 54, "m65": 77, "f65": 66}
RI_EU = 50


def main():
    db = load_json(DATA / "database.json")
    n_note = 0
    for it in db["items"]:
        n = it["nutrition_and_sustainability"]
        p, kcal = n["macros_per_100g"]["proteins_g"], n["kcal_per_100g"]
        if p is None or "bozza" in (n.get("data_basis") or ""):
            n.setdefault("protein_reference", None)
            finalize_completeness(it)
            continue
        ref = {"protein_g_per_100g": p,
               "percent_pri_larn_adult_m": round(p / PRI["m"] * 100, 1), "percent_pri_larn_adult_f": round(p / PRI["f"] * 100, 1),
               "percent_pri_larn_over65_m": round(p / PRI["m65"] * 100, 1), "percent_pri_larn_over65_f": round(p / PRI["f65"] * 100, 1),
               "percent_ri_eu": round(p / RI_EU * 100, 1),
               "energy_from_protein_percent": round(p * 4 / kcal * 100, 1) if kcal else None, "claim_note": None}
        claims = (n.get("nutrition_claims_eu") or {}).get("it", [])
        if any("proteine" in c for c in claims) and p < 0.10 * PRI["f"]:
            ref["claim_note"] = {
                "it": f"Claim conforme al Reg. CE 1924/2006 (il {ref['energy_from_protein_percent']}% delle calorie viene dalle proteine), "
                      f"ma in valore assoluto 100 g forniscono {p} g di proteine, circa il {ref['percent_pri_larn_adult_f']}% "
                      f"del fabbisogno giornaliero raccomandato (LARN, donna adulta).",
                "en": f"Claim compliant with Reg. (EC) 1924/2006 ({ref['energy_from_protein_percent']}% of calories from protein), "
                      f"but in absolute terms 100 g provide {p} g of protein, about {ref['percent_pri_larn_adult_f']}% "
                      f"of the recommended daily intake (Italian LARN, adult woman)."}
            n_note += 1
        n["protein_reference"] = ref
        mark_enriched(it, ["nutrition_and_sustainability.protein_reference"])
        finalize_completeness(it)
    db["metadata"]["protein_reference_method"] = {"it": __doc__.split("Uso:")[0].strip(),
                                                  "pri_g_day": PRI, "ri_eu_g_day": RI_EU,
                                                  "source": "fonti_locali/Tabelle-riassuntive_SINU.pdf (LARN 2014, tabella Proteine)"}
    save_json(DATA / "database.json", db)
    print(f"protein_reference aggiunto; claim proteici contestualizzati: {n_note}")


if __name__ == "__main__":
    main()

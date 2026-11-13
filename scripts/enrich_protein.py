"""Protein reference for Italy (nutrition_and_sustainability.protein_reference).

National scientific reference: LARN - SINU, 4th revision 2014 (fonti_locali/Tabelle-riassuntive_SINU.pdf):
  adults 18-64 years PRI 0.90 g/kg/day -> 63 g/day men (70 kg), 54 g/day women (60 kg)
  65 years and over   PRI 1.1 g/kg/day  -> 77 g/day men, 66 g/day women
EU labelling reference: protein RI 50 g/day (Reg. (EU) 1169/2011, Annex XIII, part B).
Claim (Reg. (EC) 1924/2006): "source of/high in protein" = >=12% / >=20% of energy from protein.
The criterion is legal but relative: in very low-energy vegetables it triggers even with a few grams. If the 100 g
portion covers less than 10% of the LARN PRI (adult woman, 5.4 g), the claim stays (it is compliant) but comes
with a note that puts it into context.
Usage:  python scripts/enrich_protein.py
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
    print(f"protein_reference added; protein claims put into context: {n_note}")


if __name__ == "__main__":
    main()

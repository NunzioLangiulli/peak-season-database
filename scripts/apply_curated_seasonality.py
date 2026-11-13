"""Applies the hand-curated Italian seasonality (config/italy_seasonality_curated.json) to products missing
from the seasonal calendars. Does not overwrite a seasonality already computed by the vote across calendars. Idempotent.
Usage:  python scripts/apply_curated_seasonality.py   (after enrich_seasonality.py)
"""
from common import CONFIG, DATA, finalize_completeness, load_json, mark_enriched, save_json

O, P, S, E = "out_of_season", "primizie", "in_season", "end_of_season"
NAME = {"ortodacoltivare": "Orto da Coltivare", "slow_food": "Fondazione Slow Food", "provincia_cuneo_funghi": "Provincia di Cuneo, schede funghi",
        "bur_emilia_romagna_amarene": "disciplinare IGP Amarene Brusche di Modena (BUR Emilia-Romagna 2012)",
        "biblioteca_bertoliana": "Biblioteca civica Bertoliana, scheda botanica", "naturasi": "NaturaSì, schede di frutta e verdura di stagione"}


def main():
    db = load_json(DATA / "database.json")
    cfg = load_json(CONFIG / "italy_seasonality_curated.json")["items"]
    I = {i["id"]: i for i in db["items"]}
    done = []
    for iid, c in cfg.items():
        it = I.get(iid)
        if not it:
            continue
        s = it["seasonality"]
        own = s.get("italy_source", {}).get("source")
        if (s.get("italy_macro_areas") or {}).get("nord") and own is None:
            continue                     # already computed from the calendars
        if c.get("derive"):
            src = I[c["derive"]]["seasonality"]
            areas, nat = src["italy_macro_areas"], src["italy_national"]
            s["italy_source"] = {"source": "derived_" + c["derive"]}
            note = c["note"]
        else:
            m = [O] * 12
            for k, st in (("S", S), ("p", P), ("f", E)):
                for mo in c.get(k, []):
                    m[mo - 1] = st
            areas, nat = {a: m for a in ("nord", "centro", "sud_isole")}, m
            s["italy_source"] = {"source": c["source"], "url": c["url"]}
            rule_it = f" Resa: {c['rule'][0]}." if c.get("rule") else ""
            rule_en = f" Rendering: {c['rule'][1]}." if c.get("rule") else ""
            note = (f"Fonte: {NAME[c['source']]} (periodo di raccolta).{rule_it} Calendario unico applicato alle tre macro-aree; nessun picco (una sola fonte).",
                    f"Source: {NAME[c['source']]} (harvest period).{rule_en} One calendar applied to all three macro-areas; no peak (single source).")
            dc = it["data_completeness"]                 # verbatim quote: only in the internal notes (Italian)
            q = f"Stagionalità italiana, citazione da {NAME[c['source']]}: \"{c['quote']}\""
            if q not in dc["notes"]:
                dc["notes"] = (dc["notes"] + " " + q).strip()
        s["italy_macro_areas"] = {a: list(v) for a, v in areas.items()}
        s["italy_national"] = list(nat)
        s["derivation_notes"] = {"it": note[0], "en": note[1]}
        mark_enriched(it, ["seasonality.italy_macro_areas", "seasonality.italy_national"])
        finalize_completeness(it)
        done.append(iid)
    save_json(DATA / "database.json", db)
    print("curated seasonality applied:", len(done))


if __name__ == "__main__":
    main()

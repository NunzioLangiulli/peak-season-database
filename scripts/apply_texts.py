"""Applies the rewritten IT/EN texts (scripts/texts/block_*.json) to the database and generates the structured texts.

Texts written by hand by merging the sources (Altroconsumo, Greenpeace, USDA HB66, UC Davis, CREA/BDA-IEO and the
verified database values), reworked and not copied:
  sl  buying_guide.shopping_list_preview      ds  buying_guide.detailed_selection
  cs  ripening_and_storage.card_short_storage si  ripening_and_storage.storage_instructions
  cn  postharvest_physiology.chilling_injury.symptoms (only if chill-sensitive)
  hb  nutrition_and_sustainability.health_benefits_and_curiosities
  wr  nutrition_and_sustainability.culinary_waste_reduction
  pl  primary_location                        rt  ripening_type
Texts generated from templates starting from the verified data:
  ripening_badge_label, ripening_management.slow_down/speed_up, ethylene_compatibility.compatibility_notes,
  chilling_injury.symptoms (if sensitive and without a dedicated text).
Replaced draft texts are saved in data/draft_legacy_values.json.
Usage:  python scripts/apply_texts.py
"""
import glob

from common import DATA, ROOT, finalize_completeness, load_json, mark_enriched, save_json

CLS_IT = {"very_low": "molto bassa", "low": "bassa", "moderate": "moderata", "high": "alta", "very_high": "molto alta", "extremely_high": "elevatissima"}
CLS_EN = {"very_low": "very low", "low": "low", "moderate": "moderate", "high": "high", "very_high": "very high", "extremely_high": "extremely high"}
DRY = {"cece_chickpea", "lenticchia_lentil", "farro_emmer", "orzo_barley", "grano_duro_durum_wheat", "riso_rice", "avena_oat",
       "grano_saraceno_buckwheat", "arachide_peanut", "origano_oregano"}


def bil(pair):
    return {"it": pair[0], "en": pair[1]} if pair else None


def main():
    texts = {}
    for f in sorted(glob.glob(str(ROOT / "scripts" / "texts" / "block_*.json"))):
        texts.update(load_json(f))
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    names = {it["id"]: it["names"] for it in db["items"]}
    hb_sym = {k for k, v in load_json(ROOT / "scripts" / "config" / "hb66_chapter_curated.json")["items"].items() if v.get("symptoms")}
    missing = [it["id"] for it in db["items"] if it["id"] not in texts]
    if missing:
        raise SystemExit(f"Missing texts for: {missing}")
    warn = []
    for it in db["items"]:
        iid, t = it["id"], texts[it["id"]]
        r, n, bg = it["ripening_and_storage"], it["nutrition_and_sustainability"], it["buying_guide"]
        ph, eth = r["postharvest_physiology"], r["ethylene_compatibility"]
        lg = legacy["items"].setdefault(iid, {})
        if "texts" not in lg:   # keeps only the ORIGINAL draft texts (re-runs do not overwrite them)
          lg["texts"] = {"buying_guide": bg, "card_short_storage": r["card_short_storage"], "storage_instructions": r["storage_instructions"],
                       "ripening_badge_label": r["ripening_badge_label"], "ripening_management": r["ripening_management"],
                       "compatibility_notes": eth["compatibility_notes"], "chilling_symptoms": ph["chilling_injury"]["symptoms"],
                       "health_benefits_and_curiosities": n["health_benefits_and_curiosities"],
                       "culinary_waste_reduction": n["culinary_waste_reduction"], "primary_location": r["primary_location"],
                       "ripening_type": r["ripening_type"]}
        # --- testi scritti
        bg["shopping_list_preview"], bg["detailed_selection"] = bil(t["sl"]), bil(t["ds"])
        r["card_short_storage"], r["storage_instructions"] = bil(t["cs"]), bil(t["si"])
        n["health_benefits_and_curiosities"], n["culinary_waste_reduction"] = bil(t["hb"]), bil(t["wr"])
        r["primary_location"], r["ripening_type"] = t["pl"], t["rt"]
        for k, lim in (("sl", 130), ("cs", 42)):
            if len(t[k][0]) > lim or len(t[k][1]) > lim:
                warn.append(f"{iid}: {k} oltre {lim} caratteri")
        # --- template: etichetta maturazione
        if iid in DRY:
            r["ripening_badge_label"] = {"it": "Prodotto secco, a lunga conservazione", "en": "Dry product, long shelf life"}
        elif t["rt"] == "climaterico":
            r["ripening_badge_label"] = {"it": "Matura anche dopo l'acquisto", "en": "Keeps ripening after purchase"}
        else:
            r["ripening_badge_label"] = {"it": "Non matura dopo la raccolta: scegli fresco", "en": "Doesn't ripen after harvest: buy fresh"}
        # --- template: ethylene compatibility
        kaf = [names[k]["it"].split(" (")[0].lower() for k in eth["keep_away_from"]]
        kaf_en = [names[k]["en"].split(" (")[0].lower() for k in eth["keep_away_from"]]
        pc = eth["ethylene_production_class"]
        parts_it, parts_en = [], []
        if pc:
            parts_it.append(f"Produzione di etilene {CLS_IT[pc]}")
            parts_en.append(f"{CLS_EN[pc].capitalize()} ethylene production")
        if eth["sensitive_to_ethylene"] is True:
            if kaf:
                parts_it.append(f"sensibile all'etilene: tienilo lontano da {', '.join(kaf)}")
                parts_en.append(f"sensitive to ethylene: keep it away from {', '.join(kaf_en)}")
            else:
                parts_it.append("sensibile all'etilene: tienilo lontano dalla frutta che matura")
                parts_en.append("sensitive to ethylene: keep it away from ripening fruit")
        elif eth["sensitive_to_ethylene"] is False:
            parts_it.append("poco sensibile all'etilene")
            parts_en.append("low sensitivity to ethylene")
        if pc in ("high", "very_high", "extremely_high"):
            parts_it.append("conservalo separato da verdure a foglia e frutta da conservare")
            parts_en.append("store it apart from leafy greens and fruit you want to keep")
        eth["compatibility_notes"] = {"it": "; ".join(parts_it).capitalize() + ".", "en": "; ".join(parts_en).capitalize() + "."} if parts_it else None
        # --- template: gestione maturazione
        crit = ph["chilling_injury"]["critical_temperature_c"] if ph["chilling_injury"]["susceptible"] else None
        base = {"frigorifero": ("Conservalo in frigorifero, protetto dalla disidratazione", "Keep it in the fridge, protected from drying out"),
                "temperatura_ambiente": ("Tienilo in un luogo fresco, lontano da sole e fonti di calore", "Keep it in a cool place, away from sun and heat"),
                "luogo_fresco_buio": ("Tienilo in un luogo fresco, asciutto e buio", "Keep it in a cool, dry, dark place")}[t["pl"]]
        sd_it, sd_en = base[0], base[1]
        if eth["sensitive_to_ethylene"]:
            sd_it += " e lontano da frutti che producono etilene"
            sd_en += " and away from ethylene-producing fruit"
        if crit is not None and crit > 0:
            sd_it += f"; evita temperature inferiori a {crit:g} °C"
            sd_en += f"; avoid temperatures below {crit:g} °C"
        if iid in DRY:
            su = ("Non applicabile: è un prodotto secco.", "Not applicable: it is a dry product.")
        elif t["rt"] == "climaterico":
            su = ("Lascialo a temperatura ambiente in un sacchetto di carta, magari con una mela o una banana: l'etilene ne accelera la maturazione.",
                  "Leave it at room temperature in a paper bag, perhaps with an apple or banana: ethylene speeds up ripening.")
        else:
            su = ("Non matura dopo la raccolta: va scelto al giusto punto di maturazione e consumato presto.",
                  "It doesn't ripen after harvest: choose it at the right stage and eat it soon.")
        r["ripening_management"] = {"slow_down": {"it": sd_it + ".", "en": sd_en + "."}, "speed_up": {"it": su[0], "en": su[1]}}
        # --- chilling injury symptoms
        ci = ph["chilling_injury"]
        if (ci.get("lowest_safe_range_c") or iid in hb_sym) and ci.get("symptoms"):
            pass  # symptoms transcribed from USDA HB66 Tab. 1 (enrich_chilling.py): they take precedence
        elif t.get("cn"):
            ci["symptoms"] = bil(t["cn"])
        elif ci["susceptible"] is True:
            thr = f" sotto i {crit:g} °C" if crit is not None and crit > 0 else " a basse temperature"
            thr_en = f" below {crit:g} °C" if crit is not None and crit > 0 else " at low temperatures"
            ci["symptoms"] = {"it": f"Sensibile ai danni da freddo{thr}: possibili macchie, alterazioni della consistenza e perdita di sapore.",
                              "en": f"Prone to chilling injury{thr_en}: possible spots, texture changes and loss of flavour."}
        elif ci["susceptible"] is False:
            ci["symptoms"] = {"it": "Non sensibile ai danni da freddo: va conservato il più freddo possibile senza congelare.",
                              "en": "Not chilling-sensitive: store as cold as possible without freezing."}
            dc = it["data_completeness"]
            dc["not_applicable_fields"] = [p for p in dc.get("not_applicable_fields", [])
                                           if p != "ripening_and_storage.postharvest_physiology.chilling_injury.symptoms"]
        fields = ["buying_guide", "ripening_and_storage.card_short_storage", "ripening_and_storage.storage_instructions",
                  "ripening_and_storage.ripening_badge_label", "ripening_and_storage.ripening_management",
                  "ripening_and_storage.ethylene_compatibility.compatibility_notes", "ripening_and_storage.primary_location",
                  "ripening_and_storage.ripening_type", "ripening_and_storage.postharvest_physiology.chilling_injury.symptoms",
                  "nutrition_and_sustainability.health_benefits_and_curiosities", "nutrition_and_sustainability.culinary_waste_reduction"]
        mark_enriched(it, fields)
        it["data_completeness"]["notes"] += f" Testi IT/EN riscritti fondendo: {', '.join(t.get('src', []))} (2026-11-04)."
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(f"texts applied to {len(db['items'])} products; warnings: {len(warn)}")
    for w in warn:
        print("  W", w)


if __name__ == "__main__":
    main()

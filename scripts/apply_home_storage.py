"""Consiglio sintetico "dove conservarlo in casa" per ogni alimento (ripening_and_storage.home_storage).

Priorita' delle fonti:
1. UC Davis / Kader, 'Storing Fresh Fruits and Vegetables for Better Taste' (config/ucdavis_home_storage.json):
   frigorifero | matura sul bancone poi frigo | solo temperatura ambiente (dispensa ventilata per aglio, cipolle, patate);
2. USDA FoodKeeper (estimated_shelf_life_days.room_temp_mode): solo frigo | fino a maturazione | giorni in dispensa;
3. condizioni ottimali USDA HB66 / UC Davis gia' nella scheda (primary_location), per i pochi alimenti senza 1 e 2.
Le durate restano in estimated_shelf_life_days (FoodKeeper). Se UC Davis e FoodKeeper non coincidono si segue UC Davis
(guida pensata per il gusto a casa) e lo si annota.
Uso:  python scripts/apply_home_storage.py   (dopo apply_foodkeeper_modes.py)
"""
from common import DATA, ROOT, finalize_completeness, load_json, mark_enriched, save_json
from enrich_chilling import set_na

PDF = "https://homeorchard.ucanr.edu/files/115275.pdf"
DRY = {"cece_chickpea", "lenticchia_lentil", "farro_emmer", "orzo_barley", "grano_duro_durum_wheat", "riso_rice", "avena_oat",
       "grano_saraceno_buckwheat", "arachide_peanut", "origano_oregano"}
LABEL = {"fridge": ("In frigorifero", "In the fridge"),
         "counter_then_fridge": ("Fuori dal frigo finché matura, poi in frigo", "On the counter until ripe, then in the fridge"),
         "room_temperature": ("A temperatura ambiente", "At room temperature"),   # 2026-11-13: uniforme alle altre
         "cool_dry_pantry": ("In dispensa, al fresco e all'asciutto", "In a cool, dry pantry")}
UCD = {"refrigerator": "fridge", "ripen_on_counter_then_refrigerator": "counter_then_fridge", "room_temperature_only": "room_temperature"}
FK = {"fridge_only": "fridge", "until_ripe": "counter_then_fridge"}
PRIM = {"frigorifero": "fridge", "temperatura_ambiente": "room_temperature", "luogo_fresco_buio": "cool_dry_pantry"}
TIPS = {  # dalla guida UC Davis (testo e note della tabella) e da FoodKeeper
    "dagger": ("Si può tenere in frigo 1-3 giorni se lo usi subito dopo.", "It can be kept in the fridge for 1-3 days if used soon after."),
    "pantry": ("In un luogo della dispensa ben ventilato.", "In a well-ventilated spot in the pantry."),
    "both": ("Se lo consumi entro 7 giorni può stare anche fuori dal frigo.", "If eaten within 7 days it can stay out of the fridge."),
    "patata_potato": ("In dispensa ben ventilata e al buio, così non inverdisce.", "In a well-ventilated, dark pantry so it doesn't turn green."),
    "basilico_basil": ("Con i gambi in un bicchiere d'acqua.", "With the stems in a glass of water."),
    "pomodoro_tomato": ("In frigo perde sapore e non si colora.", "In the fridge it loses flavour and doesn't turn red."),
    "banana_banana": ("In frigo la buccia annerisce e non diventa dolce.", "In the fridge the skin turns black and it doesn't sweeten."),
    "anguria_watermelon": ("Intera, non più di 3 giorni in frigo: perde sapore e colore.", "Whole, no more than 3 days in the fridge: it loses flavour and colour."),
    "pera_pear": ("Matura fuori dal frigo; una volta matura dura 1-3 giorni in frigo.", "Ripen it on the counter; once ripe it keeps 1-3 days in the fridge."),
}
CUT = ("Una volta tagliato va sempre in frigorifero.", "Once cut, always keep it in the fridge.")
# Revisione 2026-11-13 (richiesta dell'utente): nell'app il consiglio compare subito sotto storage_instructions, quindi
# non deve ripeterne il contenuto. Consigli tolti perché già detti nel paragrafo: dispensa ventilata (aglio, cipolla,
# scalogno), patata, "1-3 giorni in frigo" (cetriolo, melanzana, peperone, peperoncino), pomodoro, pera, banana, basilico.
REDUNDANT = {"aglio_garlic", "cipolla_invernale_winter_onion", "scalogno_shallot", "patata_potato", "cetriolo_cucumber",
             "melanzana_eggplant", "peperone_bell_pepper", "peperoncino_chili_pepper", "pomodoro_tomato", "pera_pear",
             "banana_banana", "basilico_basil"}
NO_CUT = {"anguria_watermelon",   # il paragrafo dice già come conservarla una volta tagliata
          "basilico_basil"}       # sensibile al freddo: "in frigorifero" sarebbe un consiglio sbagliato


def home_tip(iid, loc, tip):
    """Consiglio breve: niente "una volta tagliato" per il frigorifero (ovvio) né senza luogo (frutta secca, legumi,
    spezie...); niente frasi che ripetono storage_instructions. None = l'app non mostra nulla."""
    if iid in DRY or loc is None:
        return None
    parts = [] if (tip is None or iid in REDUNDANT) else [tip]
    if loc != "fridge" and iid not in NO_CUT:
        parts.append(CUT)
    return {"it": " ".join(p[0] for p in parts), "en": " ".join(p[1] for p in parts)} if parts else None


def main():
    cfg = load_json(ROOT / "scripts" / "config" / "ucdavis_home_storage.json")["items"]
    db = load_json(DATA / "database.json")
    stats = {}
    for it in db["items"]:
        r = it["ripening_and_storage"]
        sl = r["postharvest_physiology"]["estimated_shelf_life_days"]
        mode = sl.get("room_temp_mode")
        u = cfg.get(it["id"])
        srcs, deriv = [], None
        if u:
            loc = UCD[u[0]]
            if len(u) > 2 and u[2] == "pantry":
                loc = "cool_dry_pantry"
            srcs.append("uc_davis_storing_guide" + (" (voce approssimata)" if u[1] == "approx" else ""))
            deriv = "UC Davis / Kader, Storing Fresh Fruits and Vegetables for Better Taste"
            if mode == "fridge_only" and loc != "fridge":
                deriv += "; FoodKeeper indica solo il frigorifero: seguita la guida UC Davis, pensata per il gusto"
            elif mode == "until_ripe" and loc == "fridge":
                deriv += "; FoodKeeper: a temperatura ambiente fino a maturazione, poi frigo (frutto acerbo)"
        elif mode:
            loc = FK.get(mode) or ("cool_dry_pantry" if it["id"] in DRY else "room_temperature")
            deriv = "USDA FoodKeeper"
            rd, rt = sl.get("refrigerated_days"), sl.get("room_temp_days")
            if it["id"] == "cipolla_estiva_summer_onion":
                loc = "cool_dry_pantry"   # FoodKeeper 'Onions': dispensa (come le cipolle secche della guida UC Davis)
            elif loc == "room_temperature" and rd and rt and rd[1] > rt[1]:
                loc = "fridge"   # FoodKeeper: in frigo dura di più che in dispensa
                deriv += " (in frigorifero dura più che a temperatura ambiente)"
        else:
            loc = PRIM.get(r.get("primary_location"))
            deriv = "condizioni ottimali di conservazione USDA HB66 / UC Davis (scheda post-raccolta)"
            srcs.append("usda_hb66")
        if mode:
            srcs.append("usda_foodkeeper")
        tip = TIPS.get(it["id"]) or (TIPS[u[2]] if u and len(u) > 2 else None)
        r["home_storage"] = {
            "location": loc, "label": {"it": LABEL[loc][0], "en": LABEL[loc][1]} if loc else None,
            "tip": home_tip(it["id"], loc, tip),
            "ucdavis_group": u[0] if u else None, "foodkeeper_mode": mode, "sources": srcs, "derivation": deriv}
        stats[loc] = stats.get(loc, 0) + 1
        mark_enriched(it, ["ripening_and_storage.home_storage"])
        set_na(it, [f"ripening_and_storage.home_storage.{k}" for k, v in r["home_storage"].items() if v is None])
        finalize_completeness(it)
    db["metadata"]["home_storage_legend"] = {
        "basis": "Guida UC Davis/Kader \"Storing Fresh Fruits and Vegetables for Better Taste\" + USDA FoodKeeper",
        "locations": {k: {"it": v[0], "en": v[1]} for k, v in LABEL.items()},
        "room_temp_mode": {"days": {"it": "giorni in dispensa (FoodKeeper)", "en": "days in the pantry (FoodKeeper)"},
                           "until_ripe": {"it": "a temperatura ambiente fino a maturazione", "en": "at room temperature until ripe"},
                           "fridge_only": {"it": "solo frigorifero", "en": "fridge only"}}}
    save_json(DATA / "database.json", db)
    print(stats)


if __name__ == "__main__":
    main()

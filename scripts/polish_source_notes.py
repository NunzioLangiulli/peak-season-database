"""Rewrites the source notes of each product in plain language (revision 2026-11-20, user request).

Two kinds of notes are rewritten, in Italian and English:
- ripening_and_storage.postharvest_physiology.estimated_shelf_life_days.basis (written by apply_foodkeeper_modes.py,
  enrich_foodkeeper.py, apply_home_storage.py and translated by localize_fields.py);
- seasonality.derivation_notes (written by enrich_seasonality.py).

Rules given by the user:
- no database field names in the texts (e.g. commercial_optimal_days, metadata.seasonality_method);
- home shelf life: "La fonte per le durate domestiche è USDA FoodKeeper '<entry>'." / "The source for home shelf life is ...";
  professional storage: "Per la conservazione in condizioni professionali la fonte è USDA HB66 / UC Davis." /
  "For storage life under professional conditions the source is USDA HB66 / UC Davis.";
- FoodKeeper notes are translated into Italian (the English original stays in the English text);
- seasonality: "if the sources disagree, the value most sources agree on is used", pointing to the "?" explanation
  "Stati della stagionalità" / "Seasonality states" instead of a metadata path.
Also (same request): English "storage time" becomes "shelf life" (home) / "storage life" (commercial), and the Italian
name of radicchio_radicchio is just "Radicchio" (Rosso di Treviso, Chioggia... are in notable_varieties).
The script recognises only the old wording, so it can run again safely. Run it after localize_fields.py.
Usage:  python scripts/polish_source_notes.py
"""
import re

from common import DATA, load_json, save_json

# FoodKeeper notes (Pantry/Refrigerate/Freeze tips): English original -> Italian. None = dropped (repeats the
# room-temperature sentence).
FK_NOTES = {
    "Until Ripe, then 1-2 days.": None,
    "Until Ripe, then 7 days.": None,
    "Or until ripe.": None,                                    # merged into the room-temperature sentence
    "Ripe is when this item is tender, fully developed and ready to eat.":
        "È maturo quando è tenero, completamente sviluppato e pronto da mangiare.",
    "Timeline for refrigerator applies to ripe fruit.": "La durata in frigorifero vale per il frutto maturo.",
    "Timeline for refrigerator applies to ripe fruit; skin will blacken.":
        "La durata in frigorifero vale per il frutto maturo; la buccia annerisce.",
    "Freezing guidance applies to product when sliced, with lemon juice and sugar.":
        "L'indicazione per il congelatore vale per il prodotto a fette, con succo di limone e zucchero.",
    "Store unbroken bulbs in pantry.": "Le teste intere si conservano in dispensa.",
    "Store individual cloves in refrigerator.": "Gli spicchi separati si conservano in frigorifero.",
    "Keep them in a plastic bag to retain moisture.": "Tenerle in un sacchetto di plastica per mantenerle umide.",
    "This is the recommended storage method for whole potatoes.":
        "È il metodo di conservazione consigliato per le patate intere.",
    "The United States Potato Board notes refrigeration can cause potatoes to darken during cooking and to develop an "
    "unpleasantly sweet taste.":
        "Lo United States Potato Board osserva che il frigorifero può far scurire le patate in cottura e dar loro "
        "un sapore sgradevolmente dolce.",
    "Freezer timeline applies to cooked and mashed potatoes.":
        "La durata in congelatore vale per le patate cotte e per il purè.",
    "Refrigeration may affect flavor; USDA recommends pantry storage.":
        "Il frigorifero può alterarne il sapore; USDA consiglia la conservazione in dispensa.",
    "Freezing guidance applies to cooked product.": "L'indicazione per il congelatore vale per il prodotto cotto.",
    "Freezing guidance applies to whole grapes.": "L'indicazione per il congelatore vale per gli acini interi.",
    "Keep stems in water.": "Tenere i gambi in acqua.",
    "Will start to discolor.": "Col tempo tende a scolorire.",
    "Fresh whole peppers will last longer if kept dry.": "I peperoncini freschi interi durano di più se tenuti asciutti.",
    "Peppers lose their crispness when frozen and thawed.": "Dopo congelamento e scongelamento perdono croccantezza.",
    "Freeze damage will appear.": "Il congelamento lo danneggia.",
    "Benefits from being stored in airtight containers and out of direct light.":
        "Si conserva meglio in contenitori ermetici, al riparo dalla luce diretta.",
}
FK_EN_DROP = {k for k, v in FK_NOTES.items() if v is None}
SENT = re.compile(r"(?<=\.)\s+(?=[A-Z])")

PRO_IT = "Per la conservazione in condizioni professionali la fonte è USDA HB66 / UC Davis."
PRO_EN = "For storage life under professional conditions the source is USDA HB66 / UC Davis."
FRIDGE_IT = "Durata in dispensa non stimata perché le fonti consigliano solo la conservazione in frigorifero"
FRIDGE_EN = "Pantry shelf life not estimated because the sources only advise storing it in the fridge"


def _days_it(v):
    return f"{v} giorno" if v == "1" else f"{v} giorni"


def _days_en(v):
    return f"{v} day" if v == "1" else f"{v} days"


def _notes(text, marker):
    m = re.search(marker + r" (.+?) commercial_optimal_days", text)
    return SENT.split(m.group(1).strip()) if m else []


def rewrite_basis(b):
    it, en = b["it"], b["en"]
    if "commercial_optimal_days" not in it and not it.startswith("Temperatura ambiente non indicata"):
        return None                                                     # already rewritten
    if it.startswith("Temperatura ambiente non indicata"):              # no FoodKeeper entry (HB66 / UC Davis only)
        m = re.search(r"\(HB66 ([^:]+):", it)
        ref_it = f" (USDA HB66, voce '{m.group(1)}')" if m else ""
        ref_en = f" (USDA HB66, '{m.group(1)}' entry)" if m else ""
        return {"it": FRIDGE_IT + ref_it + ".", "en": FRIDGE_EN + ref_en + "."}
    name_it = re.search(r"USDA FoodKeeper '(.+?)'", it).group(1)
    name_en = re.search(r"USDA FoodKeeper '(.+?)'", en).group(1)
    approx = "(voce approssimata)" in it
    purchase = "(dalla data di acquisto)" in it
    tail_it = " (voce del prodotto più simile)" if approx else ""
    tail_en = " (entry for the most similar product)" if approx else ""
    if purchase:
        tail_it += ", a partire dalla data di acquisto"
        tail_en += ", counted from the date of purchase"
    out_it = [f"La fonte per le durate domestiche è USDA FoodKeeper '{name_it}'{tail_it}."]
    out_en = [f"The source for home shelf life is USDA FoodKeeper '{name_en}'{tail_en}."]
    notes_en = _notes(en, "FoodKeeper notes:")
    or_ripe = "Or until ripe." in notes_en
    if "solo in frigorifero" in it or "Temperatura ambiente non indicata" in it:
        out_it.append(FRIDGE_IT + ".")
        out_en.append(FRIDGE_EN + ".")
    elif m := re.search(r"fino a maturazione \(poi (\S+) giorni\)", it):
        out_it.append(f"Tenere a temperatura ambiente fino a maturazione (poi {_days_it(m.group(1))}), "
                      "poi conservare in frigorifero.")
        out_en.append(f"Keep at room temperature until ripe (then {_days_en(m.group(1))}), then store in the fridge.")
    elif "fino a maturazione, poi in frigorifero" in it:
        out_it.append("Tenere a temperatura ambiente fino a maturazione, poi conservare in frigorifero.")
        out_en.append("Keep at room temperature until ripe, then store in the fridge.")
    elif m := re.search(r"in dispensa per (\S+) giorni", it):
        d = m.group(1)
        out_it.append(f"A temperatura ambiente si conserva {_days_it(d)}" + (", oppure fino a maturazione." if or_ripe else "."))
        out_en.append(f"Keeps {_days_en(d)} at room temperature" + (", or until ripe." if or_ripe else "."))
    else:
        raise ValueError(f"unknown room-temperature wording: {it}")
    if "congelamento sconsigliato" in it:
        out_it.append("Congelamento sconsigliato.")
        out_en.append("Freezing not recommended.")
    kept = [n for n in notes_en if n not in FK_EN_DROP]
    for n in kept:
        if n not in FK_NOTES:
            raise ValueError(f"FoodKeeper note without an Italian translation: {n}")
    if kept:
        out_it.append("Note di FoodKeeper: " + " ".join(FK_NOTES[n] for n in kept))
        out_en.append("FoodKeeper notes: " + " ".join(kept))
    out_it.append(PRO_IT)
    out_en.append(PRO_EN)
    return {"it": " ".join(out_it), "en": " ".join(out_en)}


VOTE_IT = re.compile(r"Stati calcolati per voto tra fonti \(metodo in metadata\.seasonality_method\)\.")
VOTE_EN = re.compile(r"States computed by voting across sources \(method in metadata\.seasonality_method\)\.")
NEW_VOTE_IT = ("Se le fonti non sono d'accordo, si usa il dato su cui concorda il maggior numero di fonti "
               "(vedi la spiegazione «Stati della stagionalità»).")
NEW_VOTE_EN = ("If the sources disagree, the value most sources agree on is used "
               "(see the explanation “Seasonality states”).")
EN_SOURCE_NAMES = [("EUFIC (Italia)", "EUFIC (Italy)"), ("Orto da Coltivare (raccolta per area)", "Orto da Coltivare (harvest by area)")]


def rewrite_derivation(d):
    it, en = d["it"], d["en"]
    new_it = VOTE_IT.sub(NEW_VOTE_IT, it)
    new_en = VOTE_EN.sub(NEW_VOTE_EN, en)
    for a, b in EN_SOURCE_NAMES:
        new_en = new_en.replace(a, b)
    return None if (new_it, new_en) == (it, en) else {"it": new_it, "en": new_en}


EN_FIXES = [("Information regarding storage time is sourced from USDA FoodKeeper.",
             "Shelf life information comes from USDA FoodKeeper."),
            ("storage times from USDA FoodKeeper", "shelf life from USDA FoodKeeper")]
NAMES_IT = {"radicchio_radicchio": "Radicchio"}


def fix_en(o):
    """Applies EN_FIXES to every {it, en} text inside o; returns the number of changed texts."""
    n = 0
    if isinstance(o, dict):
        if isinstance(o.get("en"), str) and isinstance(o.get("it"), str):
            new = o["en"]
            for a, b in EN_FIXES:
                new = new.replace(a, b)
            if new != o["en"]:
                o["en"] = new
                n += 1
        for v in o.values():
            n += fix_en(v)
    elif isinstance(o, list):
        for v in o:
            n += fix_en(v)
    return n


def main():
    db = load_json(DATA / "database.json")
    n_basis = n_der = 0
    for it in db["items"]:
        sl = it["ripening_and_storage"]["postharvest_physiology"]["estimated_shelf_life_days"]
        if isinstance(sl.get("basis"), dict) and (new := rewrite_basis(sl["basis"])):
            sl["basis"] = new
            n_basis += 1
        se = it["seasonality"]
        if isinstance(se.get("derivation_notes"), dict) and (new := rewrite_derivation(se["derivation_notes"])):
            se["derivation_notes"] = new
            n_der += 1
        fix_en(it["ripening_and_storage"])
        if it["id"] in NAMES_IT and it["names"]["it"] != NAMES_IT[it["id"]]:
            it["names"]["it"] = NAMES_IT[it["id"]]
            syn = it["names"].get("synonyms", {}).get("it")
            if isinstance(syn, list) and NAMES_IT[it["id"]] in syn:
                syn.remove(NAMES_IT[it["id"]])
            print("renamed:", it["id"], "->", NAMES_IT[it["id"]])
    save_json(DATA / "database.json", db)
    print(f"storage notes rewritten: {n_basis}; seasonality notes rewritten: {n_der}")


if __name__ == "__main__":
    main()
